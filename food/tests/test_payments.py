from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from food.models import Order, Vendor
from food.services.payment_service import initialize_payment, verify_payment


class FakeResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._payload = json_data

    def json(self):
        return self._payload

    @property
    def ok(self):
        return 200 <= self.status_code < 300


@override_settings(
    PAYSTACK_SECRET_KEY="test-secret",
    PAYSTACK_BASE_URL="https://api.paystack.test",
    BASE_URL="https://example.test",
)
class PaymentServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="user@test.com")
        self.vendor = Vendor.objects.create(business_name="Test Vendor")
        self.order = Order.objects.create(
            user=self.user,
            vendor=self.vendor,
            total=Decimal("100.00"),
            status="CONFIRMED",
            payment_status="PENDING",
        )

    @patch("food.services.payment_service._request_json")
    def test_initialize_payment_success_updates_order(self, mock_request):
        mock_response = FakeResponse(
            status_code=200,
            json_data={
                "status": True,
                "message": "Payment initialized",
                "data": {"authorization_url": "https://paystack.com/pay/xyz"}
            },
        )
        mock_request.return_value = (mock_response, mock_response.json())

        url, reference = initialize_payment(self.order)
        self.assertIn("paystack.com", url)
        self.assertTrue(reference.startswith(f"ORDER-{self.order.id}"))