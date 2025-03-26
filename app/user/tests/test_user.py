"""
Test for the user API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse


from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")


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

    def test_create_token_for_user(self):
        """Test generate token for valid credentials."""
        user_credentials = {
            "username": "user1",
            "email": "test@example.com",
            "password": "pass123",
            "name": "Test User"
        }
        create_user(**user_credentials)
        payload = {
            "username": user_credentials["username"],
            "email": user_credentials["email"],
            "password": user_credentials["password"],
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_do_not_create_token_for_bad_credentials(self):
        """Test do not generate token and return error for bad credentials."""
        create_user(username="gooduser",
                    email="test@example.com",
                    password="goodpasword"
                    )
        payload = {
            "username": "baduser",
            "email": "test1@example.com",
            "password": "badpassword",
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_for_blank_password(self):
        """Test do not return token and return error for blank password."""
        payload = {
            "username": "baduser",
            "email": "test@example.com",
            "password": "",
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)