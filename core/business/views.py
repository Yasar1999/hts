import hashlib
import hmac

from django.contrib.auth.models import Group
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache
# Create your views here.
import logging
from rest_framework.generics import GenericAPIView
import razorpay
from base.basemail import send_email_in_thread
from base.generic_functions import generate_random_string, get_base_url
from users.models import CustomUser
from django.conf import settings
from base.views import CustomPagination
from business.models import Order
from business.serializers import OrderSerializer, OrderCreateSerializer, OrderCreateRequestAPISerializer, \
    OrderItemCreateSerializer
from product.models import ProductSizeChart
from core.custom_auth import CustomJWTAuthentication
from product.serializers import ProductQuantityDetailSerializer, ProductAddToCartCreateAPISerializer

order_logger = logging.Logger(__name__)

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


class AddToCartViewSet(GenericAPIView):
    authentication_classes = [CustomJWTAuthentication]
    serializer_class = ProductAddToCartCreateAPISerializer
    my_tags = ["Order Management - Cart"]

    def post(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        cache_key = f"cart_product_{user.id}"
        cached_product_ids = cache.get(cache_key, [])
        product_ids = data.get("product_ids", [])
        # if not isinstance(product_ids, list):
        #     product_ids = [product_ids]
        # # Add new product IDs, ensuring no duplicates
        # new_product_ids = list(set(cached_product_ids + product_ids))

        # Update cache
        cache.set(cache_key, product_ids, timeout=600)

        return Response({"msg": "Added to Cart Successfully"}, status=status.HTTP_201_CREATED)

    def get(self, request, *args, **kwargs):
        user = request.user
        cache_key = f"cart_product_{user.id}"
        cached_product_ids = cache.get(cache_key, [])

        if not cached_product_ids:
            return Response({"totalRecords": 0, "records": []}, status=status.HTTP_200_OK)

        product_ids = [product['productQuantityId'] for product in cached_product_ids]

        products = ProductSizeChart.objects.filter(id__in=product_ids)
        serialized_data = ProductQuantityDetailSerializer(
            instance=products, context={"request": request}, many=True
        ).data

        return Response(
            {"totalRecords": len(serialized_data), "records": serialized_data},
            status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('clear_cart', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('pk', openapi.IN_QUERY, type=openapi.TYPE_INTEGER)
        ])
    def delete(self, request, *args, **kwargs):
        user = request.user
        cache_key = f"cart_product_{user.id}"
        cached_product_ids = cache.get(cache_key, [])

        clear_cart = request.query_params.get('clear_cart', 'false').lower() == 'true'
        pk = request.query_params.get('pk')

        if clear_cart:
            if not cached_product_ids:
                return Response({"error": "Cart is already empty"}, status=status.HTTP_400_BAD_REQUEST)
            cache.delete(cache_key)
            return Response({"msg": "Cart cleared successfully"}, status=status.HTTP_200_OK)

        if not pk:
            return Response({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        pk = int(pk)
        if pk in cached_product_ids:
            cached_product_ids.remove(pk)
            cache.set(cache_key, cached_product_ids, timeout=600)
            return Response({"msg": "Product removed from cart"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Product not found in cart"}, status=status.HTTP_404_NOT_FOUND)


class OrderViewSet(viewsets.ModelViewSet):
    authentication_classes = [CustomJWTAuthentication]
    serializer_class = OrderSerializer
    queryset = Order.objects.select_related('customer', 'managed_by').order_by('-ordered_on')
    # filter_backends = (DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter)
    # search_fields = ('order_', 'size__age', 'brand__display_name')
    # filterset_class = ProductFilter
    pagination_class = CustomPagination
    # ordering_fields = ('size__category__display_name', 'brand__display_name', 'created_on', 'last_updated_on',
    #                    'is_active',)
    my_tags = ["Order Management - Order"]

    @swagger_auto_schema(operation_description="This API is used to place the order",
                         request_body=OrderCreateRequestAPISerializer, responses={201: OrderSerializer,
                                                                                  400: 'Something went wrong'})
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        try:
            # Save order within a transaction block
            with transaction.atomic():
                # Handle guest user scenario
                if user.groups.first().display_name != "Guest":
                    customer_data = data.pop('customer', None)
                    guest_group = Group.objects.get(display_name='Guest')

                    if customer_data:
                        # Generate password
                        password = generate_random_string()

                        # Check if user already exists to prevent duplication
                        existing_user = CustomUser.objects.filter(username=customer_data['username']).first()

                        if existing_user:
                            user_instance = existing_user
                        else:
                            created_user = CustomUser.objects.create_user(
                                username=customer_data['username'],
                                phone_number=customer_data['phone_number'],
                                email=customer_data['email'],
                                password=password
                            )
                            created_user.groups.add([guest_group.id])
                            created_user.save()

                            # Send email after ensuring user is created successfully
                            current_site = get_base_url(request)
                            subject = 'HTMS: Guest User Creation'
                            recipients = [customer_data['email']]
                            template_name = 'email/user_creation.html'
                            template_data = {
                                'user': created_user.__dict__,
                                'base_logo_path': current_site,
                                'password': password
                            }
                            send_email_in_thread(subject, recipients, template_name, template_data)

                            user_instance = created_user

                        data.update({'customer': user_instance.id, 'managed_by': user.id})

                    else:
                        return Response({"error": "Customer data is required for non-guest users."},
                                        status=status.HTTP_400_BAD_REQUEST)
                else:
                    data['customer'] = user.id
                # Serialize and validate the order
                order_serializer = OrderCreateSerializer(data=data, context={'request': request})
                if not order_serializer.is_valid():
                    order_logger.error(f"Order validation failed: {order_serializer.errors}")
                    error_message = order_serializer.errors.get('non_field_errors', ['Something went wrong.'])[0]

                    return Response({"errors": error_message}, status=status.HTTP_400_BAD_REQUEST)

                order_instance = order_serializer.save()
                order_items = data.pop('order', [])

                for item in order_items:
                    item.update({'order': order_instance.id})
                    order_item_serializer = OrderItemCreateSerializer(data=item)

                    if not order_item_serializer.is_valid():
                        order_logger.error(f"Order item validation failed: {order_item_serializer.errors}")
                        transaction.set_rollback(True)  # Rollback the transaction on error
                        return Response({"errors": order_item_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

                    order_item_serializer.save()

                amount = int(order_instance.total_price * 100)
                razorpay_order = razorpay_client.order.create({
                    "amount": amount,
                    "currency": "INR",
                    "payment_capture": 1
                })
                order_instance.gateway_order_id = razorpay_order["id"]
                order_instance.save()

                return Response({
                    "message": "Order Placed Successfully",
                    "razorpay_order_id": razorpay_order["id"],
                    "amount": amount,
                    "currency": "INR"
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            order_logger.error(f"Transaction failed: {str(e)}")
            return Response({"error": "Something went wrong. Please try again."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @csrf_exempt
    @transaction.atomic
    @action(detail=False, methods=["post"], url_path='verify-payment')
    def verify_payment(self, request):
        data = request.data

        try:
            razorpay_order_id = data.get("razorpay_order_id")
            razorpay_payment_id = data.get("razorpay_payment_id")
            razorpay_signature = data.get("razorpay_signature")

            if not (razorpay_order_id and razorpay_payment_id and razorpay_signature):
                return Response({"error": "Missing required parameters"}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch the order from the database
            try:
                order_instance = Order.objects.get(gateway_order_id=razorpay_order_id)
            except Order.DoesNotExist:
                return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

            # Verify the Razorpay signature
            secret = settings.RAZORPAY_KEY_SECRET
            generated_signature = hmac.new(
                secret.encode(),
                f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
                hashlib.sha256
            ).hexdigest()

            if generated_signature == razorpay_signature:
                # Payment is successful, Update Order Status
                order_instance.gateway_payment_id = razorpay_payment_id
                order_instance.gateway_signature_id = razorpay_signature
                order_instance.payment_status = 'Success'
                order_instance.is_paid = True
                order_instance.save()

                return Response({"message": "Payment Verified!"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Payment Verification Failed!"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






