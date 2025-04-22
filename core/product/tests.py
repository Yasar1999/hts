from django.test import TestCase
from rest_framework.test import APIClient
from users.models import CustomUser
from .models import Brand
import pytest

def get_auth_token():
    CustomUser.objects.create_user(username='yasar', email='yasar@mail.com', password='Admin@123', is_superuser=True)
    client = APIClient()
    response = client.post('/api-token-auth/', {'username': 'yasar', 'password': 'Admin@123'})
    assert response.status_code == 200
    token = response.json()['access']
    return token

# Create your tests here.
@pytest.mark.django_db
class TestBrandViewSet:

    def test_get_brand_list(self):
        client = APIClient()
        token = get_auth_token()

        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        Brand.objects.create(name="vv_dress", display_name="VV Dress", description="VVD")

        response = client.get('/api/brand/')
        assert response.status_code == 200
        data = response.json()['records']
        assert len(data) == 1
        assert data[0]['display_name'] == 'VV Dress'

    def test_create_brand_list(self):
        client = APIClient()
        token = get_auth_token()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # Create a brand
        request_data = {'display_name': 'VV Dress', 'description': 'VVD'}
        response = client.post('/api/brand/', request_data, format='json')
        assert response.status_code == 201

        # Verify brand exists
        get_response = client.get('/api/brand/')
        data = get_response.json()['records']
        assert len(data) == 1
        assert data[0]['display_name'] == 'VV Dress'

    def test_duplicate_brand(self):
        client = APIClient()
        token = get_auth_token()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # First creation
        request_data = {'display_name': 'VV Dress', 'description': 'VVD'}
        response = client.post('/api/brand/', request_data, format='json')
        assert response.status_code == 201

        # Duplicate creation
        duplicate_response = client.post('/api/brand/', request_data, format='json')
        assert duplicate_response.status_code == 208
        assert duplicate_response.json()['error'] == "Brand Already Exists"


