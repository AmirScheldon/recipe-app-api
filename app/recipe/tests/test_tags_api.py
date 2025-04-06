"""
Tests for the tag APIs.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import (
    Tag,
    Recipe
)

from recipe.serializers import TagSerializer


TAGS_URL = reverse("recipe:tag-list")


def detail_tag_url(tag_id):
    """Create and return detail tag url."""
    return reverse("recipe:tag-detail", args=[tag_id])


def create_user(username="username",
                email="username@example.com",
                password="password"):

    """Create and retun user."""
    return get_user_model().objects.create_user(
        username=username,
        email=email,
        password=password
        )


class PublicTagsAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving tags."""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_tags(self):
        """Test retrieving a list of tags."""
        Tag.objects.create(user=self.user, name="tag1")
        Tag.objects.create(user=self.user, name="tag2")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_the_user(self):
        """Test retireving tags that linked to the user."""
        another_user = create_user(username="user2", email="user2@example.com")
        Tag.objects.create(user=another_user, name="Tag2")
        tag = Tag.objects.create(user=self.user, name="tag1")

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], tag.name)
        self.assertEqual(res.data[0]["id"], tag.id)

    def test_update_tag(self):
        """Test updating a tag."""
        tag = Tag.objects.create(
                                user=self.user,
                                name="Tag name before update"
                                )
        payload = {"name": "name updated"}
        url = detail_tag_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        """Test deleting a tag."""
        tag = Tag.objects.create(user=self.user, name="tag1")
        url = detail_tag_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(user=self.user).exists())

    def test_filter_tags_assigned_to_recipes(self):
        """Test listing tags to those assigned to recipes."""
        tag1 = Tag.objects.create(
            name="tag1",
            user=self.user
        )
        tag2 = Tag.objects.create(
            name="tag2",
            user=self.user
        )
        recipe = Recipe.objects.create(
            user=self.user,
            title="recipe1",
            price=Decimal("1.23"),
            time_minutes=2
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filter_tags_unique(self):
        """Test filtered tags returns a unique value."""
        tag1 = Tag.objects.create(
            name="tag1",
            user=self.user
        )
        Tag.objects.create(
            name="tag2",
            user=self.user
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
            price=Decimal("1.23"),
            time_minutes=2
        )

        recipe1.tags.add(tag1)
        recipe2.tags.add(tag1)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)
