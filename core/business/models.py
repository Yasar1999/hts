from django.db import models
from django.db.models import F
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from core.product.models import ProductSizeChart
from core.users.models import CustomUser

# Create your models here.
PAYMENT_MODE_CHOICES = [
    ('Cash', 'Cash'),
    ('Card', 'Card'),
    ('UPI', 'UPI')
]

PAYMENT_STATUS_CHOICES = [
    ('Success', 'Success'),
    ('Pending', 'Pending'),
    ('Failed', 'Failed')
]


class Order(models.Model):
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='customer')
    managed_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='customer_service', null=True,
                                   blank=True)
    ordered_on = models.DateTimeField(auto_now=True, editable=False, blank=True,
                                      help_text="When this item was ordered")
    total_price = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_quantity = models.CharField(max_length=6, null=True, blank=True)
    payment_mode = models.CharField(max_length=5, choices=PAYMENT_MODE_CHOICES, db_index=True)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    gateway_order_id = models.CharField(max_length=255, blank=True, null=True)
    gateway_payment_id = models.CharField(max_length=255, blank=True, null=True)
    gateway_signature_id = models.CharField(max_length=255, blank=True, null=True)
    is_paid = models.BooleanField(default=False)

    objects = models.Manager()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order')
    item = models.ForeignKey(ProductSizeChart, on_delete=models.CASCADE, related_name='order_item')
    quantity = models.CharField(max_length=4)

    objects = models.Manager()


@receiver(post_delete, sender=Order)
def post_delete_handler(sender, instance, **kwargs):
    """Handles cleanup after an Order instance is deleted."""
    # Perform any cleanup actions here
    instance.customer.delete()
    print(f"Order {instance.id} has been deleted.")


# @receiver(post_save, sender=OrderItem)
# def post_save_handler(sender, instance, **kwargs):
#     try:
#         product_quantity = ProductQuantity.objects.get(id=instance.item_id)
#         current_quantity = int(product_quantity.quantity)
#         new_quantity = current_quantity - int(instance.quantity)
#         product_quantity.quantity = str(new_quantity)
#         product_quantity.save(update_fields=['quantity'])
#         print(f"Product Quantity {product_quantity.id} updated successfully")
#     except ProductQuantity.DoesNotExist:
#         print(f"Error: ProductQuantity with ID {instance.item_id} does not exist")


