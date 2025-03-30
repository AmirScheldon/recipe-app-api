"""
Tests for models.
"""

from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


class ModelTests(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test creating a user with email successful."""
        username = "test"
        email = "test@example.com"
        password = "testpass123"

        user = get_user_model().objects.create_user(
            username=username,
            email=email,
            password=password
        )

        self.assertEqual(user.username, username)
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_create_new_user_email_normalized(self):
        """Test email is normalized for new users."""
        sample_emails = [
            ('test@EXAMPLE.COM', 'test@example.com'),
            ('Test2@Example.com', 'Test2@example.com'),
            ('Test3@EXAMPLE.com', 'Test3@example.com'),
            ('Test4@example.COM', 'Test4@example.com'),
        ]

        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(
                username=email.split("@")[0],
                email=email,
                password='test123'
            )
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test that creating an user without an email raises ValueError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                username="test",
                email="",
                password="test123"
            )

    def test_create_superuser(self):
        """Test creating superuser."""
        user = get_user_model().objects.create_superuser(
            username="test",
            email="test@example.com",
            password="test123"
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """Test creation recipe is succesful."""
        user = get_user_model().objects.create_user(
                username="test",
                email="test@example.com",
                password="test123"
                )
        recipe = models.Recipe.objects.create(
            user=user,
            title="Sample recipe name",
            time_minutes=5,
            price=Decimal("5.05"),
            description="Smaple recipe description."
        )

        self.assertEqual(str(recipe), recipe.title)
