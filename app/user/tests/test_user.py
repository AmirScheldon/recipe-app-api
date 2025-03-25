"""
Test for the user API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse


from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse("user:create")


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the public features of the user API."""

    def setUp(self):
        self.client = APIClient()

    def test_create_new_user_success(self):
        """Test creating a user is successful."""
        payload = {
            "username": "user",
            "email": "test@example.com",
            "password": "pass123",
            "name": "Test User"
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)

    def test_user_with_email_exists_error(self):
        """Test if user created an account with same email returns an error."""
        payload = {
            "username": "user1",
            "email": "test@example.com",
            "password": "pass123",
            "name": "Test User"
        }
        create_user(**payload)
        payload["username"] = "user2"
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_with_username_exists_error(self):
        """Test if user created an account with same username \
            returns an error."""
        payload = {
            "username": "user1",
            "email": "test@example.com",
            "password": "pass123",
            "name": "Test User"
        }
        create_user(**payload)
        payload["email"] = "test2@example.com"
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test if password is shorter than 5 chars return an error."""
        payload = {
            "username": "user1",
            "email": "test@example.com",
            "password": "pass",
            "name": "Test User"
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload["email"]
        ).exists()
        self.assertFalse(user_exists)
