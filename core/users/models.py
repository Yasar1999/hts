from django.contrib.auth.models import AbstractUser, Group
from django.db import models

# Create your models here.
from base.models import BaseModel

Group.add_to_class('last_updated_on', models.DateTimeField(auto_now=True, editable=False, blank=True,null=True))
Group.add_to_class('created_on', models.DateTimeField(auto_now_add=True, editable=False, blank=True,null=True))
Group.add_to_class('display_name', models.CharField(max_length=30))


GENDER_TYPES = (
    ('Male', "Male"),
    ('Female', "Female")
)


class CustomUser(AbstractUser, BaseModel):
    phone_number = models.PositiveBigIntegerField(null=True, blank=True)
    is_temporary_password = models.BooleanField(default=True)
    address = models.TextField(blank=True)
    gender = models.CharField(max_length=7, choices=GENDER_TYPES, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.username


def get_exclude_codes():
    from django.contrib.contenttypes.models import ContentType
    EXCLUDE_PERMISSION_CONTENT_TYPES = []

    COMMON_PERMISSION_EXCLUDE_CONTENT_TYPES = ContentType.objects.filter(app_label__in=['admin', 'sessions', 'common',
                                                                                        'base', 'logger', 'contenttypes',
                                                                                        'main', 'viewer']).\
        values_list('id', flat=True)
    UNUSED_PERMISSION_CONTENT_TYPES = ContentType.objects.filter(model__in=['productquantity', 'blacklistedtoken',
                                                                            'outstandingtoken']).values_list('id', flat=True)

    EXCLUDE_PERMISSION_CONTENT_TYPES.extend(COMMON_PERMISSION_EXCLUDE_CONTENT_TYPES)
    EXCLUDE_PERMISSION_CONTENT_TYPES.extend(UNUSED_PERMISSION_CONTENT_TYPES)


    EXCLUDE_PERMISSION_CODES = []

    USER_PERMISSION_EXCLUDE_CODES = ['add_permission', 'delete_group', 'delete_user', 'view_permission',
                                     'change_permission', 'delete_permission', 'delete_user', 'add_passwordresettokens',
                                     'view_passwordresettokens', 'change_passwordresettokens', 'delete_customuser',
                                     'delete_passwordresettokens']
    EXCLUDE_PERMISSION_CODES.extend(USER_PERMISSION_EXCLUDE_CODES)
    return EXCLUDE_PERMISSION_CONTENT_TYPES, EXCLUDE_PERMISSION_CODES