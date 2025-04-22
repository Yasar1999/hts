from core.base.serializers import BaseSerializer
from rest_framework import serializers
from .models import Category, Product, ProductColor, SizeChart, Brand, ProductRating, ProductSizeChart
import django_filters


class CategorySerializer(BaseSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class BrandSerializer(BaseSerializer):
    class Meta:
        model = Brand
        fields = "__all__"


class SizeChartSerializer(BaseSerializer):
    category_detail = CategorySerializer(source='category', read_only=True)

    class Meta:
        model = SizeChart
        fields = "__all__"


class CategoryCreateUpdateAPISerializer(BaseSerializer):
    class Meta:
        model = Category
        fields = ["display_name", "classification", "section"]


class BrandCreateUpdateAPISerializer(BaseSerializer):
    class Meta:
        model = Brand
        fields = ["display_name", "description"]


class SizeChartCreateUpdateAPISerializer(BaseSerializer):
    class Meta:
        model = SizeChart
        fields = ["size", "age", "category", "row", "column", "max_percentage"]


class ProductSizeChartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSizeChart
        fields = "__all__"


class ProductColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductColor
        fields = "__all__"


class ProductSerializer(BaseSerializer):
    class Meta:
        model = Product
        fields = "__all__"

    def to_representation(self, instance):
        primitive_repr = super().to_representation(instance)
        # brand = instance.brand
        # size = instance.size
        # category = size.category
        # primitive_repr['classification'] = category.classification
        # primitive_repr['brand_name'] = brand.display_name
        # primitive_repr['category_name'] = category.display_name
        # primitive_repr['category'] = category.id
        # primitive_repr['size_value'] = size.size
        #
        # # Fetch product quantities efficiently
        # product_quantities = list(instance.product.all())
        #
        # # Compute total quantity
        # total_quantity = sum(int(pq.quantity) for pq in product_quantities)
        # primitive_repr['product_quantity'] = total_quantity
        #
        # # Optimize color-quantity representation
        # primitive_repr['product_colors'] = [
        #     {'color': pq.color, 'quantity': pq.quantity, 'id': pq.id}
        #     for pq in product_quantities
        # ]

        return primitive_repr


class ProductRetrieveSerializer(BaseSerializer):

    class Meta:
        model = Product
        fields = ['id', 'product_code', 'max_price', 'image']

    def to_representation(self, instance):
        primitive_repr = super(ProductRetrieveSerializer, self).to_representation(instance)
        # brand = instance.brand
        # size = instance.size
        # category = size.category
        # primitive_repr['size'] = size.size
        # primitive_repr['age'] = size.age
        # primitive_repr['category'] = category.display_name
        # primitive_repr['row'] = size.row
        # primitive_repr['column'] = size.column
        # primitive_repr['section'] = category.section
        # primitive_repr['brand'] = brand.display_name
        # primitive_repr['description'] = brand.description
        # product_quantities = instance.product.all()
        # primitive_repr['product_color_quantity'] = ProductColorSerializer(product_quantities, many=True).data

        return primitive_repr


class ProductFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name='created_on__date', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='created_on__date', lookup_expr='lte')
    # category = django_filters.CharFilter(field_name='size__category__id')
    # age = django_filters.CharFilter(field_name='size__age')
    # min_price = django_filters.CharFilter(field_name='min_price', lookup_expr='gte')
    # max_price = django_filters.CharFilter(field_name='max_price', lookup_expr='lte')

    class Meta:
        model = Product
        fields = ['start_date', 'end_date',]


class ProductRatingSerializer(BaseSerializer):

    class Meta:
        model = ProductRating
        fields = "__all__"


class ProductRatingCreateUpdateAPISerializer(BaseSerializer):

    class Meta:
        model = ProductRating
        fields = ['rating', 'comment']


class ProductRetrieveDetailSerializer(BaseSerializer):

    class Meta:
        model = Product
        fields = ['id', 'product_code',]

    def to_representation(self, instance):
        primitive_repr = super(ProductRetrieveDetailSerializer, self).to_representation(instance)
        # brand = instance.brand
        # size = instance.size
        # category = size.category
        # primitive_repr['size'] = size.size
        # primitive_repr['age'] = size.age
        # primitive_repr['category'] = category.display_name
        # primitive_repr['brand'] = brand.display_name
        # primitive_repr['description'] = brand.description

        return primitive_repr


class ProductQuantityDetailSerializer(serializers.ModelSerializer):
    product_detail = ProductRetrieveDetailSerializer(source='product', read_only=True)

    class Meta:
        model = ProductColor
        # exclude = ["quantity",]
        fields = "__all__"


class ProductAddToCartCreateAPISerializer(serializers.Serializer):
    product_ids = serializers.IntegerField(required=True)

