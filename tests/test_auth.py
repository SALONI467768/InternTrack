import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

@pytest.mark.django_db
class TestAuthentication:
    def setup_method(self):
        self.client = APIClient()

    def test_user_registration_success(self):
        payload = {
            'email': 'new_candidate@interntrack.ai',
            'full_name': 'Taylor Swift',
            'password': 'StrongPassword@123',
            'password_confirm': 'StrongPassword@123',
            'role': 'STUDENT'
        }
        response = self.client.post('/api/auth/register/', payload)
        assert response.status_code == 201
        assert 'tokens' in response.data
        assert 'access' in response.data['tokens']
        assert response.data['user']['email'] == 'new_candidate@interntrack.ai'
        assert response.data['user']['role'] == 'STUDENT'

        # Verify User and Profile were created
        user = User.objects.get(email='new_candidate@interntrack.ai')
        assert user.profile.full_name == 'Taylor Swift'

    def test_user_registration_password_mismatch(self):
        payload = {
            'email': 'bad_pass@interntrack.ai',
            'full_name': 'Test User',
            'password': 'StrongPassword@123',
            'password_confirm': 'DifferentPassword@123',
            'role': 'STUDENT'
        }
        response = self.client.post('/api/auth/register/', payload)
        assert response.status_code == 400
        assert 'password_confirm' in response.data

    def test_user_login_success(self):
        user = User.objects.create_user(email='login_user@interntrack.ai', password='SecretPassword@123')
        payload = {
            'email': 'login_user@interntrack.ai',
            'password': 'SecretPassword@123'
        }
        response = self.client.post('/api/auth/login/', payload)
        assert response.status_code == 200
        assert 'tokens' in response.data
        assert response.data['user']['email'] == 'login_user@interntrack.ai'

    def test_user_login_invalid_credentials(self):
        response = self.client.post('/api/auth/login/', {
            'email': 'nonexistent@interntrack.ai',
            'password': 'WrongPassword123'
        })
        assert response.status_code == 401
