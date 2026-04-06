from django.test import TestCase
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ValidationError

from food.models import Category, Food, Order, OrderItem, Review, Vendor
from food.services.review_service import create_review


class CreateReviewServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="password123",
        )
        self.other_user = User.objects.create_user(
            username="bob",
            email="bob@example.com",
            password="password123",
        )
        self.vendor = Vendor.objects.create(
            user=self.user,
            business_name="Tasty Foods",
            address="123 Main St",
            city="Lagos",
            state="Lagos",
            country="Nigeria",
            is_active=True,
            is_approved=True,
        )
        self.category = Category.objects.create(
            name="Snacks",
            slug="snacks",
        )
        self.food = Food.objects.create(
            vendor=self.vendor,
            category=self.category,
            name="Meat Pie",
            price="5.00",
            stock=10,
        )
        self.second_food = Food.objects.create(
            vendor=self.vendor,
            category=self.category,
            name="Sausage Roll",
            price="6.00",
            stock=5,
        )

    def _create_order(self, status="DELIVERED"):
        order = Order.objects.create(
            user=self.user,
            vendor=self.vendor,
            status=status,
        )
        OrderItem.objects.create(order=order, food=self.food, quantity=1)
        OrderItem.objects.create(order=order, food=self.second_food, quantity=2)
        return order

    def test_only_order_owner_can_review(self):
        order = self._create_order()
        with self.assertRaises(ValidationError):
            create_review(
                order=order,
                user=self.other_user,
                validated_data={"rating": 5, "comment": "Great!"},
            )

    def test_only_delivered_orders_can_be_reviewed(self):
        order = self._create_order(status="PENDING")
        with self.assertRaises(ValidationError):
            create_review(
                order=order,
                user=self.user,
                validated_data={"rating": 4, "comment": "Good"},
            )

    def test_duplicate_review_is_blocked(self):
        order = self._create_order()
        create_review(
            order=order,
            user=self.user,
            validated_data={"rating": 5, "comment": "Nice"},
        )

        with self.assertRaises(ValidationError):
            create_review(
                order=order,
                user=self.user,
                validated_data={"rating": 3, "comment": "Second review"},
            )

        self.assertEqual(Review.objects.filter(order=order).count(), 1)

    def test_review_sets_vendor_and_invalidates_cache(self):
        order = self._create_order()
        food_keys = [
            f"food_reviews_stats_{self.food.id}",
            f"food_reviews_stats_{self.second_food.id}",
        ]
        vendor_key = f"vendor_reviews_stats_{self.vendor.id}"

        for key in food_keys + [vendor_key]:
            cache.set(key, {"average_rating": 5, "total_reviews": 1}, timeout=300)

        review = create_review(
            order=order,
            user=self.user,
            validated_data={
                "rating": 4,
                "comment": "Solid meal",
                "vendor": None,
                "order": None,
            },
        )

        self.assertEqual(review.vendor, order.vendor)
        for key in food_keys + [vendor_key]:
            self.assertIsNone(cache.get(key))
