from rest_framework import serializers
from datetime import datetime
from core.users.models import CustomUser


class SafeCurrentUserDefault(serializers.CurrentUserDefault):
    """Custom CurrentUserDefault that handles missing request context."""

    def __call__(self, serializer_field):
        request = serializer_field.context.get("request", None)
        return request.user if request and hasattr(request, "user") else None


class BaseSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(
        default=serializers.CreateOnlyDefault(SafeCurrentUserDefault()),
        queryset=CustomUser.objects.all()
    )
    last_updated_by = serializers.PrimaryKeyRelatedField(
        default=SafeCurrentUserDefault(),
        queryset=CustomUser.objects.all()
    )
    created_on = serializers.DateTimeField(
        default=serializers.CreateOnlyDefault(datetime.now()),
        read_only=True
    )
    last_updated_on = serializers.DateTimeField(
        default=datetime.now(),
        read_only=True
    )

    class Meta:
        abstract = True

    def to_representation(self, instance):
        primitive_repr = super().to_representation(instance)
        created_by = None
        created_by__id = None
        last_updated_by = None
        if instance.created_by:
            created_by_first_name = str(instance.created_by.first_name) if instance.created_by.first_name else ''
            created_by_last_name = str(instance.created_by.last_name) if instance.created_by.last_name else ''
            created_by = f'{created_by_first_name} {created_by_last_name}'
            created_by__id = instance.created_by.id

        if instance.last_updated_by:
            last_updated_by_first_name = str(
                instance.last_updated_by.first_name) if instance.last_updated_by.first_name else ''
            last_updated_by_last_name = str(
                instance.last_updated_by.last_name) if instance.last_updated_by.last_name else ''
            last_updated_by = f'{last_updated_by_first_name} {last_updated_by_last_name}'

        primitive_repr['created_by'] = created_by
        # primitive_repr['created_by__id'] = created_by__id
        primitive_repr['last_updated_by'] = last_updated_by
        return primitive_repr
