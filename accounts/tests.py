from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class RegistrationTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="testuser@test.com", password="TestPass@123")
    
    def test_register_success(self):
        data = {
            "username": "sobur",
            "email": "sobur@test.com",
            "password": "TestPass@123",
            "password2": "TestPass@123",
        }
        response = self.client.post(reverse('register'), data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="sobur").exists())
        
    def test_register_password_mismatch(self):
        data = {
            "username": "sobur",
            "email": "sobur@test.com",
            "password": "TestPass@123",
            "password2": "TestPass@124",
        }
        response = self.client.post(reverse('register'), data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(User.objects.count() == 1)
        
    def test_register_duplicate_email(self):
        data = {
            "username": "sobur",
            "email": "testuser@test.com",
            "password": "TestPass@123",
            "password2": "TestPass@123",
        }
        response = self.client.post(reverse('register'), data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_register_missing_fields(self):
        data = {
            "username": "sobur",
            "email": "",
            "password": "TestPass@123",
            "password2": "TestPass@123",
        }
        response = self.client.post(reverse('register'), data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@test.com",
            password="TestPass@123"
        )
    
    def test_login_success(self):
        data = {
            "username": "testuser",
            "password": "TestPass@123",
        }
        response = self.client.post(reverse('login'), data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
    def test_login_wrong_password(self):
        data = {
            "username": "testuser",
            "password": "blablapass",
        }
        response = self.client.post(reverse('login'), data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('access', response.data)
        
    def test_login_nonexistent_user(self):
        data = {
            "username": "sobur",
            "password": "TestPass@123",
        }
        response = self.client.post(reverse('login'), data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('access', response.data)
        
    def test_token_refresh_success(self):
        data = {
            "username": "testuser",
            "password": "TestPass@123",
        }
        response = self.client.post(reverse('login'), data)
        refresh = response.data['refresh']
        
        response = self.client.post(reverse('token_refresh'), {'refresh': refresh})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        
    def test_token_refresh_invalid(self):
        response = self.client.post(reverse('token_refresh'), {'refresh': 'garbage'})
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@test.com",
            password="TestPass@123"
        )
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        
    def test_logout_blacklists_refresh_token(self):
        data = {
            "username": "testuser",
            "password": "TestPass@123",
        }
        response = self.client.post(self.login_url, data)
        access = response.data['access']
        refresh = response.data['refresh']
        
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access)
        response = self.client.post(self.logout_url, {'refresh': refresh})
        
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        
        response = self.client.post(reverse('token_refresh'), {'refresh': refresh})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_logout_unauthenticated(self):
        data = {
            "username": "testuser",
            "password": "TestPass@123",
        }
        response = self.client.post(self.login_url, data)
        refresh = response.data['refresh']
        
        response = self.client.post(self.logout_url, {'refresh': refresh})
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_logout_invalid_refresh_token(self):
        data = {
            "username": "testuser",
            "password": "TestPass@123",
        }
        response = self.client.post(self.login_url, data)
        access = response.data['access']
        
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access)
        response = self.client.post(self.logout_url, {'refresh': "garbage"})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_protected_endpoint_with_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + "garbage")
        response = self.client.post(self.logout_url, {'refresh': "garbage"})
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

