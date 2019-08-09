from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class GroupTests(APITestCase):
    def setUp(self):
        self.create_group()

    def create_group(self):
        self.group = Group.objects.create(name="administrator")

    def test_create_group(self):
        url = reverse("group-list")
        data = {"name": "test"}
        response = self.client.post(url, data, format="json")
        group = Group.objects.last()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Group.objects.count(), 2)
        self.assertEqual(group.name, "test")

    def test_get_group_list(self):
        url = reverse("group-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_get_group_detail(self):
        url = reverse("group-detail", kwargs={"pk": self.group.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.group.name)

    def test_update_group(self):
        url = reverse("group-detail", kwargs={"pk": self.group.id})
        response = self.client.put(url, {"name": "admin"})
        self.group.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Group.objects.count(), 1)
        self.assertEqual(self.group.name, "admin")

    def test_partial_update_group(self):
        url = reverse("group-detail", kwargs={"pk": self.group.id})
        response = self.client.patch(url, {"name": "test"})
        self.group.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Group.objects.count(), 1)
        self.assertEqual(self.group.name, "test")
