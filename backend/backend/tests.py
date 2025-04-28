import os

from rest_framework.test import APITestCase
from rest_framework import status

from django.test import TestCase
from django.urls import reverse
from django.db import connection

# auto-close db connection after tests

def tearDownModule():
    # Close the Django connection nicely
    connection.close()

# tests for user registration and login
class UserAuthTests(APITestCase):
    
    def test_user_registration(self):
        url = reverse('register')  # from urls.py 'name' field
        data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], "User created successfully.")

    def test_user_login(self):
        # register
        self.client.post(reverse('register'), {'username': 'testuser', 'password': 'testpassword123'}, format='json')

        # login
        response = self.client.post(reverse('token_obtain_pair'), {'username': 'testuser', 'password': 'testpassword123'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
