import configparser
import os
import random
import re
import string

from django.conf import settings


def get_traceback(self, exc_info=None):
    """Helper function to return the traceback as a string"""
    import traceback
    import sys
    return '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))


def get_property_values(section, key):
    path = os.path.join(settings.BASE_DIR, 'property.ini')
    config = configparser.ConfigParser()
    config.read(path)
    try:
        return config.get(section, key)
    except Exception:
        return ''

def get_permission_values(section, key):
    path = os.path.join(settings.BASE_DIR, 'permission.ini')
    config = configparser.ConfigParser()
    config.read(path)
    try:
        return config.get(section, key)
    except Exception:
        return ''

def get_base_url(request):
    scheme = request.scheme
    host = request.get_host()
    base_url = f"{scheme}://{host}"
    return base_url

def get_name_slug(name_value):
    # Current Method
    # name = name_value.replace(' ', '_').strip().lower()

    # Change to
    name = name_value.strip().lower()
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name


def generate_random_string():
    # Select random characters from letters and digits
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choices(characters, k=7))
    return random_string
