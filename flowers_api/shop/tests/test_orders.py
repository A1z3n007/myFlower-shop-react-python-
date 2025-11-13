from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth.models import User

from shop.models import Coupon, Order, Product, SavedAddress
from shop.views import _sign_photo


class OrderFlowTests(APITestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Rose Garden",
            category="roses",
            price=1000,
            image_url="https://example.com/rose.jpg",
        )
        self.coupon = Coupon.objects.create(
            code="LOVE10",
            discount_type=Coupon.DiscountType.PERCENT,
            value=10,
        )

    def test_order_creation_with_coupon_and_events(self):
        payload = {
            "customer_name": "Alice",
            "customer_phone": "+77000000000",
            "email": "alice@example.com",
            "address": "Blue street 1",
            "total": 1000,
            "coupon_code": "LOVE10",
            "items": [
                {"product_id": self.product.id, "qty": 2},
            ],
        }
        resp = self.client.post("/api/orders/", payload, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        data = resp.json()
        self.assertEqual(data["discount_amount"], 200)
        self.assertEqual(len(data["items_info"]), 1)
        self.assertEqual(len(data["events"]), 1)

    def test_saved_address_crud(self):
        user = User.objects.create_user(username="bob@example.com", password="123456")
        client = APIClient()
        client.force_authenticate(user=user)
        payload = {
            "label": "Дом",
            "address": "Green way 5",
            "is_default": True,
        }
        resp = client.post("/api/account/addresses/", payload, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(SavedAddress.objects.filter(user=user).count(), 1)
        resp = client.get("/api/account/addresses/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["items"]), 1)
        addr_id = resp.json()["items"][0]["id"]
        resp = client.delete("/api/account/addresses/", {"id": addr_id}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(SavedAddress.objects.filter(user=user).count(), 0)

    def test_delivery_photo_upload(self):
        order = Order.objects.create(
            customer_name="T",
            email="t@example.com",
            address="test",
            total=0,
        )
        token = _sign_photo.sign(str(order.id))
        photo = SimpleUploadedFile("photo.jpg", b"fakeimage", content_type="image/jpeg")
        resp = self.client.post(
            f"/api/orders/photo/{token}/",
            {"photo": photo},
        )
        self.assertEqual(resp.status_code, 200)
        order.refresh_from_db()
        self.assertIsNotNone(order.delivery_photo)
