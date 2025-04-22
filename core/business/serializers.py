from rest_framework import serializers
from .models import Order, OrderItem
from core.product.serializers import ProductQuantityDetailSerializer
# from product.models import ProductQuantity


class OrderCustomerCreateSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, max_length=100)
    phone_number = serializers.IntegerField()
    email = serializers.EmailField(allow_blank=True)

    """{
  "order": [
    {
      "quantity": "1",
      "item": 1
    },
    {
      "quantity": "1",
      "item": 2
    }
  ],
  "managed_by": {
    "username": "vishal",
    "phone_number": 9885488712,
    "email": ""
  },
  "total_price": "250",
  "total_quantity": "2"
}"""


class OrderItemSerializer(serializers.ModelSerializer):
    item_detail = ProductQuantityDetailSerializer(source='item')

    class Meta:
        model = OrderItem
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    order_item = OrderItemSerializer(source='order', many=True)

    class Meta:
        model = Order
        fields = "__all__"


class OrderItemCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderItem
        fields = "__all__"


class OrderCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Order
        fields = "__all__"

    def validate(self, data):
        """Check if the items are available and validate order details"""
        initial_data = self.initial_data
        order_item = initial_data.get('order', [])
        product_total_price, order_total_quantity = 0, 0

        # for order in order_item:
        #     # Fetch the product along with its related product details
        #     product_available_check = ProductQuantity.objects.select_related('product').filter(id=order['item']).first()
        #
        #     if not product_available_check:
        #         raise serializers.ValidationError(f"Product does not exist!")
        #
        #     if int(product_available_check.quantity) < 1:
        #         raise serializers.ValidationError(f"Product '{product_available_check.product.brand.display_name}' "
        #                                           f"is out of stock.")
        #
        #     # Check the ordered quantity is available
        #     quantity = int(order['quantity'])
        #     price = product_available_check.product.min_price
        #
        #     if quantity > int(product_available_check.quantity):
        #         raise serializers.ValidationError(
        #             f"The selected product '{product_available_check.product.brand.display_name}' has only "
        #             f"{product_available_check.quantity} available.")
        #
        #     order_total_quantity += quantity
        #     product_total_price += price * quantity
        #
        # # Validate total quantity
        # if int(data['total_quantity']) != order_total_quantity:
        #     raise serializers.ValidationError("Total quantity and ordered quantity do not match.")
        #
        # # Validate total price
        # if product_total_price > int(data['total_price']):
        #     raise serializers.ValidationError("Total price provided is less than the actual price.")

        return data


class OrderCreateRequestAPISerializer(serializers.ModelSerializer):
    order_item = OrderItemCreateSerializer(many=True)
    customer = OrderCustomerCreateSerializer()

    class Meta:
        model = Order
        exclude = ("managed_by", )
