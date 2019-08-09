from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from user.models import User


class UserTests(APITestCase):
    def setUp(self):
        self.create_user()

    def create_user(self):
        self.user = User.objects.create(username="test_username",
                                        email="test@test.com")

    def test_create_user(self):
        url = reverse("user-list")
        data = {"username": "rick_dalton",
                "email": "rickdalton@gmail.com"}
        response = self.client.post(url, data, format="json")
        user = User.objects.last()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(user.username, "rick_dalton")

    def test_get_user_list(self):
        url = reverse("user-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_get_user_detail(self):
        url = reverse("user-detail", kwargs={"pk": self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user.username)

    def test_update_user(self):
        url = reverse("user-detail", kwargs={"pk": self.user.id})
        response = self.client.put(url, {"username": "cliff_booth",
                                         "email": "cliff_booth@gmail.com"})
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(self.user.username, "cliff_booth")
        self.assertEqual(self.user.email, "cliff_booth@gmail.com")

    def test_partial_update_user(self):
        url = reverse("user-detail", kwargs={"pk": self.user.id})
        response = self.client.patch(url, {"username": "marvin_schwarz"})
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(self.user.username, "marvin_schwarz")
