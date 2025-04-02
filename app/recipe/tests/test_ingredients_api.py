"""
Tests for Ingredient API.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Ingredient

from recipe.serializers import IngredientSerializer


INGREDIENT_URL = reverse("recipe:ingredient-list")


def create_user(username="username",
                email="username@example.com",
                password="password"):

    """Create and retun user."""
    return get_user_model().objects.create_user(
        username=username,
        email=email,
        password=password
        )


class PublicIngredientAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retriving ingredients."""
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientAPITests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieves_ingredient(self):
        """Test retrieve ingredients for authenticated user."""
        Ingredient.objects.create(user=self.user, name="ingredient1")
        Ingredient.objects.create(user=self.user, name="ingredient2")

        res = self.client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test list of ingredients is limited to authenticated user."""
        another_user = create_user(username="username1",
                                   email="username1@example.com")
        Ingredient.objects.create(user=another_user, name="ingredient1")
        ingredient = Ingredient.objects.create(user=self.user,
                                               name="ingredient2")

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], ingredient.name)
        self.assertEqual(res.data[0]["id"], ingredient.id)
