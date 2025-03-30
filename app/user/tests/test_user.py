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
ME_URL = reverse("user:me")


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

    def test_retrieve_user_unauthenticate(self):
        """Test authentication is required for users."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API request that required authentication."""

    def setUp(self):
        self.user = create_user(
            username="test",
            email="test@example.com",
            password="test123",
            name="Test name"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in users."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            "name": self.user.name,
            "username": self.user.username,
            "email": self.user.email
        })

    def test_post_request_to_me_endpoint_not_allowed(self):
        """Test POST is not allowed to me endpoint."""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for authenticated users."""
        payload = {
            "name": "New name",
            "password": "newpassword"
        }
        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload["name"])
        self.assertTrue(self.user.check_password(payload["password"]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
