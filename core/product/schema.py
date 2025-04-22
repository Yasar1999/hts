import graphene
from graphene_django.types import DjangoObjectType
from .models import Product


# Create a GraphQL Type for Product
class ProductType(DjangoObjectType):
    class Meta:
        model = Product


# Define Query
class Query(graphene.ObjectType):
    all_products = graphene.List(ProductType)


    def resolve_all_products(root, info):
        return Product.objects.all()


# Create Schema
schema = graphene.Schema(query=Query)
