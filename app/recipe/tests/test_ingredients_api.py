"""
Tests for Ingredient API.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import (
    Ingredient,
    Recipe,
)

from recipe.serializers import IngredientSerializer


INGREDIENT_URL = reverse("recipe:ingredient-list")


def ingredient_detail_url(ingredient_id):
    """Create and return an ingredient detail URL."""
    return reverse("recipe:ingredient-detail", args=[ingredient_id])


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

    def test_update_ingredient(self):
        """Test updating an ingredient."""
        ingredient = Ingredient.objects.create(user=self.user, name="Egg")
        payload = {
            "name": "Oil"
        }

        url = ingredient_detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload["name"])

    def test_delete_ingredient(self):
        """Test deleting ingredients."""
        ingredient = Ingredient.objects.create(user=self.user, name="Egg")

        url = ingredient_detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())

    def test_filter_ingredients_assigned_to_recipes(self):
        """Test listing ingredients by these assigned to recipes."""
        in1 = Ingredient.objects.create(
            user=self.user,
            name="ingredient1"
        )
        in2 = Ingredient.objects.create(
            user=self.user,
            name="ingredient2"
        )
        recipe = Recipe.objects.create(
            user=self.user,
            title="recipe1",
            price=Decimal("1.23"),
            time_minutes=2
        )
        recipe.ingredients.add(in1)

        res = self.client.get(INGREDIENT_URL, {"assigned_only": 1})

        s1 = IngredientSerializer(in1)
        s2 = IngredientSerializer(in2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_ingredients_unique(self):
        """Test filtered ingredients returns a unique value."""
        ing = Ingredient.objects.create(
            user=self.user,
            name="ingredient1"
        )
        Ingredient.objects.create(
            user=self.user,
            name="ingredient2"
        )
        recipe1 = Recipe.objects.create(
            user=self.user,
            title="recipe1",
            price=Decimal("1.23"),
            time_minutes=2
        )
        recipe2 = Recipe.objects.create(
            user=self.user,
            title="recipe2",
            price=Decimal("1.22"),
            time_minutes=4
        )
        recipe1.ingredients.add(ing)
        recipe2.ingredients.add(ing)

        res = self.client.get(INGREDIENT_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)
