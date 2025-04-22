from datetime import datetime

import django_filters
from rest_framework import serializers
from django.contrib.auth.models import Group, Permission
from core.base.serializers import BaseSerializer
from .models import CustomUser


class PermissionSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        primitive_repr = super(PermissionSerializer, self).to_representation(instance)
        primitive_repr['category'] = instance.content_type.app_label

        return primitive_repr

    class Meta:
        model = Permission
        fields = ('id', 'content_type', 'name', 'codename')


class GroupListSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(read_only=True, many=True)

    class Meta:
        model = Group
        fields = "__all__"


class CustomUserSerializer(BaseSerializer):

    class Meta:
        model = CustomUser
        fields = ["username", "first_name", "last_name", "phone_number", "is_active", "address", "gender", "email",
                  "date_of_birth", "groups", "created_by", "last_updated_by", "created_on", "last_updated_on"]

    # def validate_username(self, value):
    #     if not value:
    #         raise serializers.ValidationError("Username is required")


class CustomUserListSerializer(BaseSerializer):
    role = GroupListSerializer(source='groups', read_only=True, many=True)

    class Meta:
        model = CustomUser
        fields = ["id", "username", "first_name", "is_superuser", "last_name", "phone_number", "is_active", "address",
                  "gender", "email", "is_temporary_password", "date_of_birth", "groups", "role", "created_by",
                  "last_updated_by", "created_on", "last_updated_on"]


class CustomUserFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name='created_on', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='created_on', lookup_expr='lte')
    groups = django_filters.CharFilter(field_name='groups')
    is_active = django_filters.BooleanFilter(field_name='is_active')

    class Meta:
        model = CustomUser
        fields = ['start_date', 'end_date', 'groups', 'is_active']


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["name", "display_name", "permissions"]


class PermissionsUpdateApiSerializer(serializers.ModelSerializer):
    codename_list = serializers.ListField()

    class Meta:
        model = CustomUser
        fields = ['codename_list']


class CustomUserPasswordRequestSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(required=True, max_length=15)
    new_password = serializers.CharField(required=True, max_length=15)
    confirm_password = serializers.CharField(required=True, max_length=15)

    class Meta:
        model = CustomUser
        fields = ["old_password", "new_password", "confirm_password"]

