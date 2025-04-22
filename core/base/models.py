from django.db import models
# Create your models here.
from django.utils import timezone
from drf_yasg.inspectors import SwaggerAutoSchema

from core.settings import AUTH_USER_MODEL


class BaseModel(models.Model):
    """
        Useful abstract base class that adds the concept of something being active,
        having a user that created or modified the item and creation and modification
        dates.
        """
    is_active = models.BooleanField(default=True,
                                    help_text="Whether this item is active, use this instead of deleting")

    created_by = models.ForeignKey(AUTH_USER_MODEL,
                                   related_name="%(app_label)s_%(class)s_creations",
                                   help_text="The user which originally created this item", on_delete=models.SET_NULL,
                                   null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True, editable=False, blank=True,
                                      help_text="When this item was originally created")

    last_updated_by = models.ForeignKey(AUTH_USER_MODEL,
                                        related_name="%(app_label)s_%(class)s_modifications",
                                        help_text="The user which last modified this item", on_delete=models.SET_NULL,
                                        null=True, blank=True)
    last_updated_on = models.DateTimeField(auto_now=True, editable=False, blank=True,
                                           help_text="When this item was last modified")
    is_deleted = models.BooleanField(default=False, help_text='use this for soft deleting')

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields', None)

        if (update_fields is None or 'last_updated_on' in update_fields) and not kwargs.pop('preserve_last_updated_on',
                                                                                            False):
            self.last_updated_on = timezone.now()

        return super(BaseModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class CustomAutoSchema(SwaggerAutoSchema):

    def get_tags(self, operation_keys=None):
        tags = self.overrides.get('tags', None) or getattr(self.view, 'my_tags', [])
        if not tags:
            tags = [operation_keys[0]]

        return tags
