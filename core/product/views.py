from django.core.cache import cache
from rest_framework import permissions, viewsets, filters, status, generics
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError, ParseError
from rest_framework.generics import CreateAPIView
from .serializers import ProductSerializer, CategoryCreateUpdateAPISerializer, BrandCreateUpdateAPISerializer, \
    CategorySerializer, ProductColorSerializer, ProductFilter, BrandSerializer, SizeChartCreateUpdateAPISerializer, \
    SizeChartSerializer, ProductRetrieveSerializer, ProductRatingSerializer, ProductRatingCreateUpdateAPISerializer, \
    ProductSizeChartSerializer
from base.views import CustomPagination, CustomDjangoModelPermission, common_cache_clear
from django.db import transaction
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, ProductColor, Product, SizeChart, Brand, ProductRating, ProductSizeChart
import json
from base.generic_functions import get_name_slug
from django.shortcuts import get_object_or_404
from core.custom_auth import CustomJWTAuthentication

# Create your views here.


class CategoryViewSet(viewsets.ModelViewSet):
    authentication_classes = [CustomJWTAuthentication]
    serializer_class = CategorySerializer
    queryset = Category.objects.all().order_by('-last_updated_on')
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter)
    filterset_fields = ('display_name', 'name', 'classification')
    search_fields = ('name', 'display_name', 'classification')
    pagination_class = CustomPagination
    ordering_fields = ('name', 'display_name', 'created_on', 'last_updated_on', 'created_by', 'last_updated_by',
                       'is_active')
    my_tags = ["Product Management - Category"]

    def get_permissions(self):
        if self.action in ['list']:
            return []
        else:
            return [permissions.IsAuthenticated(), CustomDjangoModelPermission()]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        cache_key = f"user_{user.id}_category"

        cached_accounts = cache.get(cache_key)
        if cached_accounts is not None:
            return cached_accounts

        if not user.is_superuser:
            queryset = queryset.filter(is_active=True)

        cache.set(cache_key, queryset, timeout=300)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        pagination_queryset = self.paginate_queryset(queryset)
        total_records = queryset.count()
        _serializer_data = CategorySerializer(pagination_queryset, many=True, context={'request': request}).data

        return Response({"totalRecords": total_records, "records": _serializer_data},
                        status=status.HTTP_200_OK)


    @swagger_auto_schema(operation_description="Permissions = ['product.add_category'] ,To create Category ",
                         request_body=CategoryCreateUpdateAPISerializer, responses={201: CategorySerializer})
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = request.data
        cat_obj = Category.objects.filter(name__iexact=get_name_slug(data['display_name']),
                                          classification=data['classification'])
        if cat_obj:
            return Response({"error": "Category Already Exists"}, status=status.HTTP_208_ALREADY_REPORTED)

        try:
            data.update({'name': get_name_slug(data['display_name'])})
            category_serializer = CategorySerializer(data=data, context={'request': request})
            category_serializer.is_valid(raise_exception=True)
            category_serializer.save()
            common_cache_clear('category', request.user.id)
            return Response({"msg": "Category created successfully"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": "Unable to process the request"}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(operation_description="Permissions = ['product.change_category'] ,To update Category ",
                         request_body=CategoryCreateUpdateAPISerializer, responses={200: CategorySerializer})
    @transaction.atomic
    def update(self, request, pk=None, *args, **kwargs):
        cat_ins = get_object_or_404(Category, id=pk)
        data = request.data
        cat_obj = Category.objects.filter(name__iexact=get_name_slug(data['display_name']),
                                          classification=data['classification']).exclude(Q(pk=pk)).first()
        if cat_obj:
            return Response({"error": "Category Already Exists"}, status=status.HTTP_208_ALREADY_REPORTED)
        try:
            data.update({'name': get_name_slug(data['display_name'])})
            category_serializer = CategorySerializer(instance=cat_ins, data=data, context={'request': request})
            category_serializer.is_valid(raise_exception=True)
            category_serializer.save()
            common_cache_clear('category', request.user.id)
            return Response({"msg": "Category updated successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Unable to process the request"}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(operation_description="Permissions = ['product.change_category'] ,To active/Inactive Category ",
                         request_body=CategoryCreateUpdateAPISerializer, responses={200: CategorySerializer})
    @transaction.atomic
    def partial_update(self, request, pk=None, *args, **kwargs):
        cat_ins = get_object_or_404(Category, id=pk)
        data = request.data
        size = SizeChart.objects.filter(category__id=pk, is_active=True)
        if 'is_active' in data and size.exists():
            response_data = {
                "error": "Category is already mapped with Size"
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        else:
            cat_serializer = self.serializer_class(cat_ins, data=data, partial=True)
            cat_serializer.is_valid(raise_exception=True)
            cat_serializer.save()
            response_data = {
                "msg": "Category Updated Successfully"
            }
            common_cache_clear('category', request.user.id)
            return Response(response_data, status=status.HTTP_200_OK)

    @transaction.atomic
    def destroy(self, request, pk=None, *args, **kwargs):
        cat_ins = get_object_or_404(Category, id=pk)
        if cat_ins.product_category.exists():
            return Response({"error": "Can't able to delete the mapped category"}, status=status.HTTP_226_IM_USED)
        cat_ins.delete()
        common_cache_clear('category', request.user.id)
        return Response({"msg": "Category deleted successfully"}, status=status.HTTP_200_OK)


class SizeChartViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, CustomDjangoModelPermission]
    authentication_classes = [CustomJWTAuthentication]
    serializer_class = SizeChartSerializer
    queryset = SizeChart.objects.select_related('category').order_by('-last_updated_on')
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter)
    filterset_fields = ('size', 'category__id', 'row', 'column', 'age')
    search_fields = ('size', 'category__name', 'row', 'column', 'age')
    pagination_class = CustomPagination
    ordering_fields = ('size', 'category__display_name', 'row', 'column', 'age' 'created_on', 'last_updated_on',
                       'created_by', 'last_updated_by', 'is_active')
    my_tags = ["Product Management - SizeChart"]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        cache_key = f"user_{user.id}_size"

        cached_accounts = cache.get(cache_key)
        if cached_accounts is not None:
            return cached_accounts

        if not user.is_superuser:
            queryset = queryset.filter(is_active=True)

        cache.set(cache_key, queryset, timeout=300)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        pagination_queryset = self.paginate_queryset(queryset)
        total_records = queryset.count()
        _serializer_data = SizeChartSerializer(pagination_queryset, many=True, context={'request': request}).data

        return Response({"totalRecords": total_records, "records": _serializer_data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_description="Permissions = ['product.add_sizechart'] ,To create Size Chart ",
                         request_body=SizeChartCreateUpdateAPISerializer, responses={201: SizeChartSerializer})
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = request.data
        size_chart_obj = SizeChart.objects.filter(size=data['size'], age__iexact=data['age'].strip(),
                                                  category__id=data['category'])
        if size_chart_obj:
            return Response({"error": "Size Already Exists"}, status=status.HTTP_208_ALREADY_REPORTED)
        try:
            size_chart_serializer = SizeChartSerializer(data=data, context={'request': request})
            size_chart_serializer.is_valid(raise_exception=True)
            size_chart_serializer.save()
            common_cache_clear('size', request.user.id)
            return Response({"msg": "Size created successfully"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(e)
            return Response({"error": "Unable to process the request"}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(operation_description="Permissions = ['product.change_sizechart'] ,To update Size Chart ",
                         request_body=SizeChartCreateUpdateAPISerializer, responses={200: SizeChartSerializer})
    @transaction.atomic
    def update(self, request, pk=None, *args, **kwargs):
        size_chart_ins = get_object_or_404(SizeChart, id=pk)
        data = request.data
        size_chart_obj = SizeChart.objects.filter(size=data['size'], age__iexact=data['age'].strip(),
                                                  category__id=data['category']).exclude(pk=pk).first()
        if size_chart_obj:
            return Response({"error": "Size Already Exists"}, status=status.HTTP_208_ALREADY_REPORTED)
        try:
            size_chart_serializer = SizeChartSerializer(instance=size_chart_ins, data=data, context={'request': request})
            size_chart_serializer.is_valid(raise_exception=True)
            size_chart_serializer.save()
            common_cache_clear('size', request.user.id)
            return Response({"msg": "Size updated successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Unable to process the request"}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Permissions = ['product.change_size'] ,To active/Inactive Size ",
        request_body=SizeChartCreateUpdateAPISerializer, responses={200: SizeChartSerializer})
    @transaction.atomic
    def partial_update(self, request, pk=None, *args, **kwargs):
        cat_ins = get_object_or_404(SizeChart, id=pk)
        data = request.data
        product = Product.objects.filter(size__id=pk, is_active=True)
        if 'is_active' in data and product.exists():
            response_data = {
                "error": "Size is already mapped with Product"
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        else:
            size_chart_serializer = self.serializer_class(cat_ins, data=data, partial=True)
            size_chart_serializer.is_valid(raise_exception=True)
            size_chart_serializer.save()
            response_data = {
                "msg": "Size Updated Successfully"
            }
            common_cache_clear('size', request.user.id)
            return Response(response_data, status=status.HTTP_200_OK)

    @transaction.atomic
    def destroy(self, request, pk=None, *args, **kwargs):
        size_chart_ins = get_object_or_404(Category, id=pk)
        if size_chart_ins.size_chart.exists():
            return Response({"error": "Can't able to delete the mapped Size"}, status=status.HTTP_226_IM_USED)
        size_chart_ins.delete()
        common_cache_clear('size', request.user.id)
        return Response({"msg": "Size deleted successfully"}, status=status.HTTP_200_OK)


class BrandViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, CustomDjangoModelPermission]
    authentication_classes = [CustomJWTAuthentication]
    serializer_class = BrandSerializer
    queryset = Brand.objects.all().order_by('-last_updated_on')
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter)
    filterset_fields = ('name', 'display_name',)
    search_fields = ('name', 'display_name',)
    pagination_class = CustomPagination
    ordering_fields = ('name', 'display_name', 'created_on', 'last_updated_on', 'created_by', 'last_updated_by',
                       'is_active')
    my_tags = ["Product Management - Brand"]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        cache_key = f"user_{user.id}_brand"

        cached_accounts = cache.get(cache_key)
        if cached_accounts is not None:
            return cached_accounts

        if not user.is_superuser:
            queryset = queryset.filter(is_active=True)

        cache.set(cache_key, queryset, timeout=300)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        pagination_queryset = self.paginate_queryset(queryset)
        total_records = queryset.count()
        _serializer_data = self.serializer_class(pagination_queryset, many=True, context={'request': request}).data

        return Response({"totalRecords": total_records, "records": _serializer_data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_description="Permissions = ['product.add_brand'] ,To create Brand ",
                         request_body=BrandCreateUpdateAPISerializer, responses={201: BrandSerializer})
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = request.data
        brand_obj = Brand.objects.filter(Q(name__iexact=get_name_slug(data['display_name'])) |
                                         Q(display_name__iexact=data['display_name'].strip())).first()
        if brand_obj:
            return Response({"error": "Brand Already Exists"}, status=status.HTTP_208_ALREADY_REPORTED)
        try:
            data.update({'name': get_name_slug(data['display_name'])})
            brand_serializer = self.serializer_class(data=data, context={'request': request})
            brand_serializer.is_valid(raise_exception=True)
            brand_serializer.save()
            common_cache_clear('brand', request.user.id)
            return Response({"msg": "Brand created successfully"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(e)
            return Response({"error": "Unable to process the request"}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(operation_description="Permissions = ['product.change_brand'] ,To update Brand ",
                         request_body=BrandCreateUpdateAPISerializer, responses={200: BrandSerializer})
    @transaction.atomic
    def update(self, request, pk=None, *args, **kwargs):
        brand_ins = get_object_or_404(Brand, id=pk)
        data = request.data
        brand_obj = Brand.objects.filter(Q(name__iexact=get_name_slug(data['display_name'])) |
                                         Q(display_name__iexact=data['display_name'].strip())).exclude(Q(pk=pk)).first()
        if brand_obj:
            return Response({"error": "Brand Already Exists"}, status=status.HTTP_208_ALREADY_REPORTED)
        try:
            data.update({'name': get_name_slug(data['display_name'])})
            brand_serializer = self.serializer_class(instance=brand_ins, data=data, context={'request': request})
            brand_serializer.is_valid(raise_exception=True)
            brand_serializer.save()
            common_cache_clear('brand', request.user.id)
            return Response({"msg": "Brand updated successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"error": "Unable to process the request"}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Permissions = ['product.change_brand'] ,To active/Inactive Brand ",
        request_body=BrandCreateUpdateAPISerializer, responses={200: BrandSerializer})
    @transaction.atomic
    def partial_update(self, request, pk=None, *args, **kwargs):
        brand_ins = get_object_or_404(Brand, id=pk)
        data = request.data
        product = Product.objects.filter(brand__id=pk, is_active=True)
        if 'is_active' in data and product.exists():
            response_data = {
                "error": "Brand is already mapped with Size"
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        else:
            brand_serializer = self.serializer_class(brand_ins, data=data, partial=True)
            brand_serializer.is_valid(raise_exception=True)
            brand_serializer.save()
            response_data = {
                "msg": "Brand Updated Successfully"
            }
            common_cache_clear('brand', request.user.id)
            return Response(response_data, status=status.HTTP_200_OK)

    @transaction.atomic
    def destroy(self, request, pk=None, *args, **kwargs):
        brand_ins = get_object_or_404(Brand, id=pk)
        if brand_ins.brand_detail.exists():
            return Response({"error": "Can't able to delete the mapped brand"}, status=status.HTTP_226_IM_USED)
        brand_ins.delete()
        common_cache_clear('brand', request.user.id)
        return Response({"msg": "Brand deleted successfully"}, status=status.HTTP_200_OK)


class ProductViewSet(viewsets.ModelViewSet):
    authentication_classes = [CustomJWTAuthentication]
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related('brand').order_by('-last_updated_on')
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter)
    search_fields = ('category__display_name', 'brand__display_name')
    filterset_class = ProductFilter
    pagination_class = CustomPagination
    ordering_fields = ('category__display_name', 'brand__display_name', 'created_on', 'last_updated_on',
                       'is_active',)
    my_tags = ["Product Management - Product"]

    def get_permissions(self):
        if self.action in ['get_products']:
            return []
        else:
            return [permissions.IsAuthenticated(), CustomDjangoModelPermission()]

    def get_queryset(self):
        user = self.request.user
        cache_key = "public_product" if self.action == 'get_products' else f"user_{user.id}_products"
        cached_accounts = cache.get(cache_key)
        if cached_accounts is not None:
            return cached_accounts

        queryset = super().get_queryset()
        if self.action == "get_products" or not user.is_superuser:
            queryset = queryset.filter(is_active=True)

        cache.set(cache_key, queryset, timeout=300)

        return queryset

    def retrieve(self, request, pk=None, *args, **kwargs):
        cache_key = f"product_detail_{pk}"
        cached_product = cache.get(cache_key)

        if cached_product:
            return Response(json.loads(cached_product), status=status.HTTP_200_OK)

        instance = self.get_object()
        _serializer_data = ProductRetrieveSerializer(instance, context={'request': request}).data

        cache.set(cache_key, json.dumps(_serializer_data), timeout=600)
        return Response(_serializer_data, status=status.HTTP_200_OK)


    def format_paginated_response(self, queryset, request):
        pagination_queryset = self.paginate_queryset(queryset)
        total_records = queryset.count()
        serializer_data = ProductSerializer(
            pagination_queryset, many=True, context={'request': request}
        ).data
        return Response(
            {"totalRecords": total_records, "records": serializer_data},
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        operation_description="To get products in unauthenticated window",
        responses={200: ProductSerializer},
    )
    @action(methods=["get"], detail=False, url_path="get-products")
    def get_products(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return self.format_paginated_response(queryset, request)

    def list(self, request, *args, **kwargs):
        return self.get_products(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Permissions = ['product.add_product'] ,To create Product ",
                         responses={201: ProductSerializer})
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                data = json.loads(request.data['data'])
                files = request.FILES
                classifications = data.pop('classification', None)

                if not classifications:
                    return Response({'error': 'At least one classification is required'},
                                    status=status.HTTP_400_BAD_REQUEST)

                for classification in classifications:
                    categories = classification.pop('categories', None)
                    if not categories:
                        continue  # Or handle as an error depending on business rules

                    for category in categories:
                        category_data = data.copy()
                        category_data.update({'category': category['category']})

                        product_serializer = ProductSerializer(data=category_data, context={'request': request})
                        product_serializer.is_valid(raise_exception=True)
                        product_instance = product_serializer.save()

                        colors = category.pop('colors', None)
                        if not colors:
                            return Response({'error': 'At least one color is required'}, status=status.HTTP_400_BAD_REQUEST)

                        for color in colors:
                            sizes = color.pop('sizes', None)
                            if not sizes:
                                return Response({'error': 'At least one size is required'}, status=status.HTTP_400_BAD_REQUEST)

                            product_image = None
                            if 'photo_key' in color and color['photo_key'] in files:
                                product_image = files.get(color['photo_key'])

                            color.update({
                                "product": product_instance.id,
                                "image": product_image
                            })

                            product_color_serializer = ProductColorSerializer(data=color)
                            product_color_serializer.is_valid(raise_exception=True)
                            product_color_instance = product_color_serializer.save()

                            for size in sizes:
                                size.update({"product_color": product_color_instance.id})
                                product_size_serializer = ProductSizeChartSerializer(data=size)
                                product_size_serializer.is_valid(raise_exception=True)
                                product_size_serializer.save()

                common_cache_clear('products', request.user.id)
                return Response({'msg': "Products created"}, status=status.HTTP_201_CREATED)

        except NotFound as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ParseError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(operation_description="Permissions = ['product.change_product'] ,To edit Product ",
                         responses={200: ProductSerializer})
    @transaction.atomic
    def update(self, request, pk=None, *args, **kwargs):
        try:
            with transaction.atomic():
                data = json.loads(request.data['data'])
                product_instance = get_object_or_404(Product, id=pk)
                files = request.FILES
                classifications = data.pop('classification', None)

                if not classifications:
                    return Response({'error': 'At least one classification is required'}, status=status.HTTP_400_BAD_REQUEST)

                product_color_ids = list(product_instance.product.all().values_list('id', flat=True))

                for classification in classifications:
                    categories = classification.pop('categories', None)
                    if not categories:
                        continue

                    for category in categories:
                        colors = category.pop('colors', None)
                        if not colors:
                            return Response({'error': 'At least one color is required'}, status=status.HTTP_400_BAD_REQUEST)

                        category_data = data.copy()
                        category_data.update({'category': category['category']})

                        product_serializer = ProductSerializer(data=category_data, instance=product_instance, context={'request': request})
                        product_serializer.is_valid(raise_exception=True)
                        product_instance = product_serializer.save()

                        for color in colors:
                            sizes = color.pop('sizes', None)
                            if not sizes:
                                return Response({'error': 'At least one size is required'}, status=status.HTTP_400_BAD_REQUEST)

                            product_image = None
                            if 'photo_key' in color and color['photo_key'] in files:
                                product_image = files.get(color['photo_key'])

                            color.update({
                                "product": product_instance.id,
                                "image": product_image
                            })

                            product_size_ids = None
                            if (color_id := color.get('id')) is not None:
                                color_instance = get_object_or_404(ProductColor, id=color_id)
                                product_size_ids = list(color_instance.product_size.all().values_list('id', flat=True))
                                if color_id in product_color_ids:
                                    product_color_ids.remove(color_id)
                                product_color_serializer = ProductColorSerializer(data=color, instance=color_instance)
                            else:
                                product_color_serializer = ProductColorSerializer(data=color)

                            product_color_serializer.is_valid(raise_exception=True)
                            product_color_instance = product_color_serializer.save()

                            for size in sizes:
                                size.update({"product_color": product_color_instance.id})
                                if (size_id := size.get('id')) is not None:
                                    product_size_instance = get_object_or_404(ProductSizeChart, id=size_id)
                                    if size_id in product_size_ids:
                                        product_size_ids.remove(size_id)
                                    product_size_serializer = ProductSizeChartSerializer(data=size, instance=product_size_instance)
                                else:
                                    product_size_serializer = ProductSizeChartSerializer(data=size)

                                product_size_serializer.is_valid(raise_exception=True)
                                product_size_serializer.save()

                            if product_size_ids:
                                ProductSizeChart.objects.filter(id__in=product_size_ids).delete()

                if product_color_ids:
                    product_instance.product.filter(id__in=product_color_ids).delete()

                common_cache_clear('products', request.user.id)
                return Response({'msg': "Products updated successfully", "id": product_instance.id}, status=status.HTTP_200_OK)

        except NotFound as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ParseError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Permissions = ['product.change_product'] ,To active/Inactive Product ",
        responses={200: ProductSerializer})
    @transaction.atomic
    def partial_update(self, request, pk=None, *args, **kwargs):
        product_ins = get_object_or_404(Product, id=pk)
        data = request.data
        product_serializer = self.serializer_class(product_ins, data=data, partial=True)
        product_serializer.is_valid(raise_exception=True)
        product_serializer.save()
        response_data = {
            "msg": f"Product {product_ins.product_code} is {'Activated' if data['is_active'] else 'Inactivated'} "
                   f"Successfully"
        }
        common_cache_clear('products', request.user.id)
        return Response(response_data, status=status.HTTP_200_OK)

    @transaction.atomic
    def destroy(self, request, pk=None, *args, **kwargs):
        product_ins = get_object_or_404(Product, id=pk)
        product_ins.delete()
        common_cache_clear('products', request.user.id)
        return Response({"msg": "Product deleted successfully"}, status=status.HTTP_200_OK)


class ProductRatingCreateAPIView(CreateAPIView):

    serializer_class = ProductRatingSerializer
    queryset = ProductRating.objects.all()
    authentication_classes = [CustomJWTAuthentication]
    my_tags = ['Product Management - Product Rating']

    @swagger_auto_schema(operation_description="To add rating for Product",
                         request_body=ProductRatingCreateUpdateAPISerializer, responses={201: ProductRatingSerializer})
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            rating_serializer = ProductRatingCreateUpdateAPISerializer(data=data, context={'request': request})
            rating_serializer.is_valid(raise_exception=True)
            rating_serializer.save()

            return Response({'msg': 'Product Rating saved successfully'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e.args[0])}, status=status.HTTP_400_BAD_REQUEST)


