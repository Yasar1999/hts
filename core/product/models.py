from django.db import models
from django.db.models.signals import post_save
from uuid import uuid4
from core.base.models import BaseModel
from colorfield.fields import ColorField
import string
from pathlib import Path
from django.core.files.storage import default_storage
import os
from django.dispatch import receiver

ALPHABET_CHOICES = [(letter, letter) for letter in string.ascii_uppercase]
NUMBER_CHOICES = [(str(digit), str(digit)) for digit in range(15)]

CLASSIFICATION_CHOICES = [
    ('Women', 'Women'),
    ('Men', 'Men'),
    ('Girl', 'Girl'),
    ('Boy', 'Boy')
]


def get_product_image_path(ins, filename):
    return os.path.join('product', 'image', str(ins.id), filename)


def save_file_field(instance, field_name, upload_to_path, *args, **kwargs):
    file_field = getattr(instance, field_name)

    if instance.id is None:  # When the instance is new
        saved_attachment = file_field
        setattr(instance, field_name, None)  # Temporarily set the file field to None
        super(instance.__class__, instance).save(*args, **kwargs)  # Save the instance

        if 'force_insert' in kwargs:
            kwargs.pop('force_insert')

        setattr(instance, field_name, saved_attachment)  # Reassign the file field after save

    super(instance.__class__, instance).save(*args, **kwargs)  # Save again with updated field


def generate_code():
    last_instance = Product.objects.all().last()
    code = "%06d"
    return code % (int(last_instance.product_code) + 1) if last_instance else code % 1


# Create your models here.
class Category(BaseModel):
    name = models.CharField(max_length=50)
    display_name = models.CharField(max_length=50)
    classification = models.CharField(max_length=10, choices=CLASSIFICATION_CHOICES, db_index=True)
    section = models.CharField(max_length=1, choices=ALPHABET_CHOICES)
    objects = models.Manager()


class SizeChart(BaseModel):
    size = models.IntegerField()
    age = models.CharField(max_length=2, null=True, blank=True)
    category = models.ForeignKey(Category, related_name='size_category', on_delete=models.CASCADE)
    row = models.CharField(max_length=2, choices=NUMBER_CHOICES)
    column = models.CharField(max_length=2, choices=NUMBER_CHOICES)
    max_percentage = models.IntegerField()

    objects = models.Manager()


class Brand(BaseModel):
    name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)

    objects = models.Manager()


# Main Table
class Product(BaseModel):
    brand = models.ForeignKey(Brand, related_name='brand_detail', on_delete=models.CASCADE)
    category = models.ForeignKey(Category, related_name='category', on_delete=models.CASCADE)
    product_code = models.CharField(max_length=6, unique=True)
    description = models.TextField(null=True, blank=True)
    objects = models.Manager()

    def save(self, *args, **kwargs):
        if not self.product_code:
            self.product_code = generate_code()
        self.save()


class ProductColor(models.Model):
    product = models.ForeignKey(Product, related_name='product', on_delete=models.CASCADE)
    image = models.ImageField(upload_to=get_product_image_path, null=True, blank=True)
    color = ColorField(default='#FF0000')

    objects = models.Manager()

    def save(self, *args, **kwargs):
        save_file_field(self, 'image', get_product_image_path, *args, **kwargs)


class ProductSizeChart(models.Model):
    product_color = models.ForeignKey(ProductColor, related_name="product_color", on_delete=models.CASCADE)
    min_price = models.DecimalField(max_digits=5, decimal_places=2)
    max_price = models.DecimalField(max_digits=5, decimal_places=2)
    size = models.ForeignKey(SizeChart, related_name="size_chart", on_delete=models.CASCADE)
    quantity = models.CharField(max_length=6)

    def save(self, *args, **kwargs):
        self.max_price = float(self.min_price) * (1 + int(self.size.max_percentage) / 100)
        self.save()


class ProductRating(BaseModel):
    product = models.ForeignKey(Product, related_name="product_rating", on_delete=models.CASCADE)
    rating = models.FloatField()
    comment = models.CharField(max_length=250)

