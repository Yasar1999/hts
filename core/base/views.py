from django.shortcuts import render

# Create your views here.
from django.utils.encoding import force_str
from django.core.cache import cache
from rest_framework.compat import coreapi
import coreschema
from rest_framework import permissions
from rest_framework.pagination import LimitOffsetPagination, _positive_int
from django.utils.translation import gettext_lazy as _
from rest_framework.response import Response
from collections import OrderedDict


class CustomDjangoModelPermission(permissions.DjangoModelPermissions):

    def __init__(self):
        self.perms_map = self.perms_map.copy()
        self.perms_map['GET'] = ['%(app_label)s.view_%(model_name)s']


class CustomPagination(LimitOffsetPagination):
    limit_query_param = 'limit'
    limit_query_description = _('Number of results to return per page.')
    offset_query_param = 'offset'
    offset_query_description = _('The initial index from which to return the results.')
    end_query_param = 'end'
    end_query_description = _('The Final index from which to return the results.')

    def paginate_queryset(self, queryset, request, view=None):
        self.limit = self.get_limit(request)
        self.count = self.get_count(queryset)
        self.offset = self.get_offset(request)
        self.end = self.get_end(request)
        self.request = request

        if self.count == 0 or self.offset > self.count:
            return []

        if self.end == 0:
            self.end = self.count
            if self.limit is not None:
                self.end = self.offset + self.limit

        if self.limit is None:
            self.limit = self.end - self.offset

        return list(queryset[self.offset:self.end])

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('totalRecords', self.count),
            ('records', data)
        ]))

    def get_count(self, queryset):
        try:
            return queryset.count()
        except (AttributeError, TypeError):
            return len(queryset)

    def get_offset(self, request):
        try:
            return _positive_int(
                request.query_params[self.offset_query_param],
            )
        except (KeyError, ValueError):
            return 0

    def get_end(self, request):
        try:
            return _positive_int(
                request.query_params[self.end_query_param],
            )
        except (KeyError, ValueError):
            return 0

    def get_limit(self, request):
        if self.limit_query_param:
            try:
                return _positive_int(
                    request.query_params[self.limit_query_param],
                    cutoff=self.max_limit
                )
            except (KeyError, ValueError):
                return None

    def get_schema_fields(self, view):
        assert coreapi is not None, 'coreapi must be installed to use `get_schema_fields()`'
        assert coreschema is not None, 'coreschema must be installed to use `get_schema_fields()`'
        return [
            coreapi.Field(
                name=self.limit_query_param,
                required=False,
                location='query',
                schema=coreschema.Integer(
                    title='Limit',
                    description=force_str(self.limit_query_description)
                )
            ),
            coreapi.Field(
                name=self.offset_query_param,
                required=False,
                location='query',
                schema=coreschema.Integer(
                    title='Offset',
                    description=force_str(self.offset_query_description)
                )
            ),
            coreapi.Field(
                name=self.end_query_param,
                required=False,
                location='query',
                schema=coreschema.Integer(
                    title='end',
                    description=force_str(self.end_query_description)
                )
            )
        ]

    def get_schema_operation_parameters(self, view):
        parameters = [
            {
                'name': self.limit_query_param,
                'required': False,
                'in': 'query',
                'description': force_str(self.limit_query_description),
                'schema': {
                    'type': 'integer',
                },
            },
            {
                'name': self.offset_query_param,
                'required': False,
                'in': 'query',
                'description': force_str(self.offset_query_description),
                'schema': {
                    'type': 'integer',
                },
            },
            {
                'name': self.end_query_param,
                'required': False,
                'in': 'query',
                'description': force_str(self.end_query_description),
                'schema': {
                    'type': 'integer',
                },
            }
        ]
        return parameters


# Cache Clear
def common_cache_clear(module, user_id):
    user = user_id or None
    if user:
        cache.delete(f"user_{user_id}_{module}")
        if module == 'products':
            cache.delete('public_product')
    else:
        cache.clear()
