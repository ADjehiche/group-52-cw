from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import timezone

from .models import Item


class ItemsCollectionViewTests(TestCase):
	def setUp(self) -> None:
		self.client = Client()
		self.owner = get_user_model().objects.create_user(username="owner", password="pass1234")

	def test_past_end_items_are_excluded(self) -> None:
		now = timezone.now()
		active = Item.objects.create(
			owner=self.owner,
			title="Active Item",
			description="Still running",
			starting_price=10,
			ends_at=now + timedelta(days=1),
		)
		Item.objects.create(
			owner=self.owner,
			title="Expired Item",
			description="Should not show",
			starting_price=5,
			ends_at=now - timedelta(days=1),
		)

		response = self.client.get("/api/items/")

		self.assertEqual(response.status_code, 200)
		data = response.json()
		ids = [item["id"] for item in data.get("items", [])]

		self.assertEqual(ids, [active.id])
