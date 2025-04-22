import logging
import re
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import Group, Permission
from django.db.models import Q
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from base.basemail import send_email_in_thread
from base.generic_functions import generate_random_string, get_base_url, get_name_slug
from .models import CustomUser, get_exclude_codes
from django.db import transaction
from rest_framework.decorators import APIView
from rest_framework import viewsets, permissions, filters, status, generics
from .serializers import CustomUserSerializer, CustomUserListSerializer, CustomUserFilter, GroupSerializer, \
    PermissionsUpdateApiSerializer, PermissionSerializer, GroupListSerializer, CustomUserPasswordRequestSerializer
from base.views import CustomDjangoModelPermission, CustomPagination

# Create your views here.

user_logger = logging.Logger(__name__)


def jwt_response_payload_handler(token, user=None, request=None):
    """ Modifying jwt login response details """
    user_details = CustomUserListSerializer(user, context={'request': request}).data

    return {
        'token': token,
        'user': user_details
    }


class CustomUserViewSet(viewsets.ModelViewSet):
    serializer_class = CustomUserListSerializer
    queryset = CustomUser.objects.all().order_by('-last_updated_on')
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter)
    search_fields = ('username', 'email', 'first_name', 'last_name', 'groups__name')
    filterset_class = CustomUserFilter
    pagination_class = CustomPagination
    ordering_fields = ('username', 'email', 'first_name', 'last_name', 'groups__name',
                       'created_on', 'last_updated_on', 'created_by', 'last_updated_by', 'is_active')
    my_tags = ["User Management - Users"]

    def get_permissions(self):
        if self.action in ['change_password']:
            return [permissions.IsAuthenticated()]
        else:
            return [permissions.IsAuthenticated(), CustomDjangoModelPermission()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(is_active=True).exclude(Q(is_superuser=True) | Q(id=self.request.user.id))
        return queryset

    @staticmethod
    def user_create(request, data):
        user_serializer = CustomUserSerializer(data=data, context={'request': request})
        user_serializer.is_valid(raise_exception=True)
        user_instance = user_serializer.save()
        password = generate_random_string()
        user_instance.set_password(password)
        user_instance.save()

        current_site = get_base_url(request)
        subject = 'HTMS: User Creation'
        recipients = [data['email']]
        template_name = 'email/user_creation.html'
        template_data = {
            'user': user_instance.__dict__,
            'base_logo_path': current_site,
            'password': password
        }
        send_email_in_thread(subject, recipients, template_name, template_data)

        return user_instance, password

    @swagger_auto_schema(operation_description="Permissions = ['users.add_customuser'] ,To create User ",
                         request_body=CustomUserSerializer, responses={201: CustomUserListSerializer})
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = request.data
        if CustomUser.objects.filter(username=data['username'].strip()).first():
            response_data = {
                "msg": "User Already Exists",
                "status": status.HTTP_208_ALREADY_REPORTED
            }
            return Response(response_data, status=status.HTTP_208_ALREADY_REPORTED)
        try:
            self.user_create(request, data)
            return Response({"msg": "User Created Successfully"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            user_logger.error(str(e))
            return Response({"error": "Invalid Input"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    @swagger_auto_schema(operation_description="Permissions = ['users.change_customuser'] ,To create User ",
                         request_body=CustomUserSerializer, responses={200: CustomUserListSerializer})
    @transaction.atomic
    def update(self, request, pk, *args, **kwargs):
        user_ins = self.get_object()
        data = request.data
        if request.method != 'PATCH':
            if CustomUser.objects.filter(username=data['username'].strip()).exclude(pk=pk).first():
                response_data = {
                    "msg": "User Already Exists",
                    "status": status.HTTP_208_ALREADY_REPORTED
                }
                return Response(response_data, status=status.HTTP_208_ALREADY_REPORTED)
        try:
            user_serializer = CustomUserSerializer(
                instance=user_ins,
                data=data,
                context={'request': request},
                partial=request.method == 'PATCH'
            )
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()
            return Response({"msg": "User Updated Successfully"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            user_logger.error(str(e))
            return Response({"error": "Invalid Input"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    @swagger_auto_schema(operation_description="To change password",
                         request_body=CustomUserPasswordRequestSerializer, responses={200: CustomUserListSerializer})
    @action(methods=['post'], detail=False, url_path='change-password')
    @transaction.atomic
    def change_password(self, request, *args, **kwargs):
        auth_user = request.user  # authenticated User
        data = request.data

        pattern = re.compile('^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$')

        # Ensure the user is authenticated and not anonymous
        if not auth_user.is_anonymous:
            # Check if the user has a temporary password
            if auth_user.is_temporary_password:
                # Verify the old password matches
                if auth_user.check_password(data['old_password'].strip()):
                    # Check if the new password follows the pattern
                    if pattern.match(data['new_password'].strip()):
                        # Ensure the new password and confirmation match
                        if data['new_password'].strip() == data['confirm_password'].strip():
                            # Set and save the new password
                            auth_user.set_password(data['new_password'].strip())
                            auth_user.is_temporary_password = False  # Reset temporary password flag
                            auth_user.save()
                            current_site = get_base_url(request)
                            subject = 'HTMS: Password Change'
                            recipients = [auth_user.email]
                            template_name = 'email/password_changed.html'
                            template_data = {
                                'user': auth_user.__dict__,
                                'base_logo_path': current_site
                            }
                            send_email_in_thread(subject, recipients, template_name, template_data)
                            return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)
                        else:
                            return Response({'error': 'New password and confirmation do not match.'},
                                            status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response({'error': 'New password does not meet security criteria.'},
                                        status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({'error': 'Old password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': 'User does not have a temporary password.'},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'User is not authenticated.'}, status=status.HTTP_401_UNAUTHORIZED)


class RoleViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Group.objects.all().order_by('-last_updated_on')
    serializer_class = GroupListSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter)
    search_fields = ('name', 'display_name')
    filterset_fields = ('name', 'display_name')
    pagination_class = CustomPagination
    ordering_fields = ('name', 'display_name', 'created_on', 'last_updated_on')
    my_tags = ["User Management - Roles"]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = request.data
        data['name'] = get_name_slug(data['display_name'])
        role_obj = Group.objects.filter(Q(name__iexact=data['name'].strip()) |
                                        Q(display_name__iexact=data['display_name'].strip())).first()
        if role_obj:
            return Response({"msg": "Role Already Exists"}, status=status.HTTP_208_ALREADY_REPORTED)
        role_serializer = GroupSerializer(data=data, context={'request': request})
        if role_serializer.is_valid():
            role_serializer.save()
            return Response({"msg": "Role Created Successfully"}, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": "Invalid Input"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    @swagger_auto_schema(operation_description="Permissions = ['auth.change_group'] ,To update Role ",
                         request_body=GroupSerializer, responses={200: GroupSerializer})
    @method_decorator(permission_required('auth.change_group', raise_exception=True), name='update')
    @transaction.atomic
    def update(self, request, pk=None, *args, **kwargs):
        role_ins = self.get_object()
        data = request.data
        data['name'] = get_name_slug(data['display_name'])
        role_serializer = GroupSerializer(role_ins, data=data)
        role_obj = Group.objects.filter(Q(name__iexact=data['name'].strip()) |
                                        Q(display_name__iexact=data['display_name'].strip())).exclude(Q(pk=pk)).first()
        if role_obj:
            return Response({"error": "Role Already Exists"}, status=status.HTTP_208_ALREADY_REPORTED)
        if role_serializer.is_valid():
            role_serializer.save()
            return Response({"msg": "Role Updated Successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid Input"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


class PermissionViewSet(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    my_tags = ["User Management - Permissions"]

    def get_queryset(self):
        EXCLUDE_PERMISSION_CONTENT_TYPES, EXCLUDE_PERMISSION_CODES = get_exclude_codes()
        query_set = self.queryset.exclude(content_type_id__in=EXCLUDE_PERMISSION_CONTENT_TYPES)
        return query_set.exclude(codename__in=EXCLUDE_PERMISSION_CODES)

    # @swagger_auto_schema(operation_description="Permissions = ['auth.change_group'] ,To update Role permissions ",
    #                      request_body=PermissionsUpdateApiSerializer, responses={200: GroupSerializer})
    # @method_decorator(permission_required('auth.change_group', raise_exception=True), name='update')
    # def update(self, request, pk=None, *args, **kwargs):
    #     data = request.data
    #     group = Group.objects.get(id=pk)
    #     permission_list = list(Permission.objects.filter(codename__in=data['codename_list']).values_list('id', flat=True))
    #     group.permissions.set(permission_list)
    #     return Response('Permission Updated Successfully', status=status.HTTP_200_OK)


class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        return Response({"msg": "Logout successful"})