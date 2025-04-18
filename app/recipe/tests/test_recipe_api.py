"""tests for recipe APIs."""
from decimal import Decimal
import tempfile
import os

from PIL import Image

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer
    )


RECIPIES_URL = reverse("recipe:recipe-list")


def url_recipe_detail(recipe_id):
    """Create and return recipe detail url."""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def image_upload_url(recipe_id):
    """Creae and return an image upload url."""
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a sample recipe."""
    defaults = {
        "title": "Sample recipe name",
        "time_minutes": 5,
        "price": Decimal("5.05"),
        "description": "Smaple recipe description.",
        "link": "http://example.com/recipe.pdf"
    }
    defaults.update(params)
    recipe = Recipe.objects.create(user=user, **defaults)

    return recipe


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(RECIPIES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            username='username',
            email='user@example.com',
            password="test1234"
            )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of all recipes."""
        create_recipe(self.user)
        create_recipe(self.user)

        res = self.client.get(RECIPIES_URL)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_recipe_list_limited_to_user(self):
        """Test list of recipe is limited to the authenticated user."""
        another_user = create_user(
            username="anotheruser",
            email="another@example.com",
            password="password123"
        )
        create_recipe(user=another_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPIES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test get recipe detail."""
        recipe = create_recipe(user=self.user)
        url = url_recipe_detail(recipe.id)
        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating recipe."""
        payload = {
            "title": "Sample recipe name",
            "time_minutes": 5,
            "price": Decimal("5.05")
        }
        res = self.client.post(RECIPIES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial update of a recipe."""
        original_link = "http://example.com/recipe.pdf"
        recipe = create_recipe(
            user=self.user,
            title="Sample recipe title",
            link=original_link
        )

        payload = {"title": "New recipe title"}
        url = url_recipe_detail(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Test full update of recipe."""
        recipe = create_recipe(
            user=self.user,
            title="Sample recipe name",
            link="http://example.com/recipe.pdf",
            description="Sample recipe description."
        )

        payload = {
            "title": "New recipe name",
            "link": "http://example.com/new-recipe.pdf",
            "description": "New recipe description.",
            "time_minutes": 5,
            "price": Decimal("5.05"),
        }
        url = url_recipe_detail(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the recipe user results in an error."""
        new_user = create_user(
            username="user2",
            email="user2@example.com",
            password="test123"
            )
        recipe = create_recipe(user=self.user)

        payload = {"user": new_user.id}
        url = url_recipe_detail(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe successful."""
        recipe = create_recipe(user=self.user)
        url = url_recipe_detail(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_recipe_other_user_delete_recipe_error(self):
        """Test trying to delete another users recipe gives error."""
        new_user = create_user(
            username="user2",
            email="user2@example.com",
            password="test123"
            )
        recipe = create_recipe(user=new_user)

        url = url_recipe_detail(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """Test creation new recipe with new tags."""
        payload = {
            "title": "Sample recipe name",
            "time_minutes": 5,
            "price": Decimal("5.05"),
            "tags": [{"name": "tag1"},
                     {"name": "tag2"}]
        }
        res = self.client.post(RECIPIES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload["tags"]:
            exists = recipe.tags.filter(
                name=tag["name"],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe wtih existing tag."""
        tag_one = Tag.objects.create(user=self.user, name="tag1")
        payload = {
            "title": "Sample recipe name",
            "time_minutes": 5,
            "price": Decimal("5.05"),
            "tags": [{"name": "tag1"},
                     {"name": "tag2"}]
        }
        res = self.client.post(RECIPIES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_one, recipe.tags.all())
        for tag in payload["tags"]:
            exists = recipe.tags.filter(
                name=tag["name"],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating tags when updating a recipe."""
        recipe = create_recipe(user=self.user)
        payload = {
            "tags": [{"name": "tag1"}]
        }
        url = url_recipe_detail(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name="tag1")
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe."""
        tag_one = Tag.objects.create(user=self.user, name="tag1")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_one)

        tag_two = Tag.objects.create(user=self.user, name="tag2")
        payload = {
            "tags": [{"name": "tag2"}]
        }
        url = url_recipe_detail(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_two, recipe.tags.all())
        self.assertNotIn(tag_one, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing a recipe tags."""
        tag = Tag.objects.create(user=self.user, name="tag1")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {
            "tags": []
        }
        url = url_recipe_detail(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        """Test creation a recipe with new ingredients."""
        payload = {
            "title": "Sample recipe name",
            "time_minutes": 5,
            "price": Decimal("5.05"),
            "ingredients": [{"name": "ingredient1"},
                            {"name": "ingredient2"}]
        }

        res = self.client.post(RECIPIES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload["ingredients"]:
            exists = recipe.ingredients.filter(
                name=ingredient["name"],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        """Test creating a new recipe with existing ingredient."""
        ingredient = Ingredient.objects.create(user=self.user,
                                               name="ingredient1")
        payload = {
            "title": "Sample recipe name",
            "time_minutes": 5,
            "price": Decimal("5.05"),
            "ingredients": [{"name": "ingredient1"},
                            {"name": "ingredient2"}]
        }

        res = self.client.post(RECIPIES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())
        for ingredient in payload["ingredients"]:
            exists = recipe.ingredients.filter(
                user=self.user,
                name=ingredient["name"]
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        """Test creatng ingredient when updating a recipe."""
        recipe = create_recipe(user=self.user)
        payload = {"ingredients": [{"name": "ingredient1"}]}

        url = url_recipe_detail(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user=self.user,
                                                name="ingredient1")
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        """Test assigning an ingredient when updating a recipe."""
        ingredient_one = Ingredient.objects.create(user=self.user,
                                                   name="ingredient1")
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient_one)

        ingredient_two = Ingredient.objects.create(user=self.user,
                                                   name="ingredient2")
        payload = {"ingredients": [{"name": "ingredient2"}]}

        url = url_recipe_detail(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient_two, recipe.ingredients.all())
        self.assertNotIn(ingredient_one, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """Test clearing a recipes ingredients."""
        ingredient = Ingredient.objects.create(user=self.user,
                                               name="ingredient")
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {"ingredients": []}
        url = url_recipe_detail(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)

    def test_filter_by_tags(self):
        """Test filtering recipes by tags."""
        r1 = create_recipe(user=self.user,
                           title="recipe1")
        r2 = create_recipe(user=self.user,
                           title="recipe2")
        t1 = Tag.objects.create(user=self.user,
                                name="tag1")
        t2 = Tag.objects.create(user=self.user,
                                name="tag2")
        r1.tags.add(t1)
        r2.tags.add(t2)
        r3 = create_recipe(user=self.user,
                           title="recipe3")

        params = {"tags": f"{t1.id},{t2.id}"}
        res = self.client.get(RECIPIES_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_by_ingredients(self):
        """Test filtering recipes by ingredients."""
        r1 = create_recipe(user=self.user,
                           title="recipe1")
        r2 = create_recipe(user=self.user,
                           title="recipe2")
        i1 = Ingredient.objects.create(user=self.user,
                                       name="ingredient1")
        i2 = Ingredient.objects.create(user=self.user,
                                       name="ingredient2")
        r1.ingredients.add(i1)
        r2.ingredients.add(i2)
        r3 = create_recipe(user=self.user,
                           title="recipe3")

        params = {"ingredients": f"{i1.id},{i2.id}"}
        res = self.client.get(RECIPIES_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


class ImageUploadTests(TestCase):
    """Tests for upload image API."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username='username',
            email='user@example.com',
            password="test1234"
            )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a recipe."""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)
            payload = {"image": image_file}
            res = self.client.post(url, payload, format="multipart")

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image."""
        url = image_upload_url(self.recipe.id)
        payload = {"image": "notanimage"}

        res = self.client.post(url, payload, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
