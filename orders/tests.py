from django.test import Client
from django.test import TestCase

from accounts.models import User
from dishes.models import Dish

from .models import Notification
from .models import Order
from .services import find_nearest_available_rider


class OrderFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.chef = User.objects.create_user(
            username="chef-test",
            email="chef-test@example.com",
            password="Strong123",
            role="chef",
            location_name="Palm Meadows",
            phone_number="9876543211",
            latitude="28.459500",
            longitude="77.026600",
        )
        self.resident = User.objects.create_user(
            username="resident-test",
            email="resident-test@example.com",
            password="Strong123",
            role="resident",
            location_name="Palm Meadows",
            phone_number="9876543212",
            latitude="28.459600",
            longitude="77.026700",
        )
        self.rider = User.objects.create_user(
            username="rider-test",
            email="rider-test@example.com",
            password="Strong123",
            role="rider",
            location_name="Palm Meadows",
            phone_number="9876543213",
            latitude="28.459700",
            longitude="77.026800",
            is_available=True,
        )
        self.dish = Dish.objects.create(
            chef=self.chef,
            name="Paneer Bowl",
            description="Healthy paneer bowl",
            meal_slot=Dish.MealSlot.LUNCH,
            price="150.00",
            quantity_available=5,
            estimated_calories=320,
            health_score="7.2",
            nutrition_notes="Paneer boosts protein but adds fat.",
            is_veg=True,
            is_published=True,
        )

    def login_resident(self):
        response = self.client.post(
            "/",
            {
                "role": "resident",
                "username": self.resident.email,
                "password": "Strong123",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def login_rider(self):
        response = self.client.post(
            "/",
            {
                "role": "rider",
                "username": self.rider.email,
                "password": "Strong123",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_add_to_cart_and_checkout_reduce_inventory(self):
        self.login_resident()

        add_response = self.client.post(
            f"/resident/cart/add/{self.dish.id}/",
            {"quantity": "2"},
            follow=True,
        )
        self.assertEqual(add_response.status_code, 200)
        self.assertContains(add_response, "Paneer Bowl was added to your cart.")

        checkout_response = self.client.post(
            "/resident/checkout/",
            {"billing_method": "cod"},
            follow=True,
        )
        self.assertEqual(checkout_response.status_code, 200)

        self.dish.refresh_from_db()
        order = Order.objects.get(resident=self.resident, dish=self.dish)
        self.assertEqual(order.quantity, 2)
        self.assertEqual(self.dish.quantity_available, 3)

    def test_checkout_rejects_non_cod_payment(self):
        self.login_resident()
        session = self.client.session
        session["cart"] = {str(self.dish.id): 1}
        session.save()

        response = self.client.post(
            "/resident/checkout/",
            {"billing_method": "card"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Only Cash on Delivery is available.")
        self.assertEqual(Order.objects.count(), 0)

    def test_busy_rider_is_skipped_for_new_assignment(self):
        second_rider = User.objects.create_user(
            username="rider-free",
            email="rider-free@example.com",
            password="Strong123",
            role="rider",
            location_name="Palm Meadows",
            phone_number="9876543214",
            latitude="28.459800",
            longitude="77.026900",
            is_available=True,
        )
        Order.objects.create(
            resident=self.resident,
            chef=self.chef,
            dish=self.dish,
            rider=self.rider,
            quantity=1,
            total_price="150.00",
            status=Order.Status.ACCEPTED,
        )
        new_order = Order.objects.create(
            resident=self.resident,
            chef=self.chef,
            dish=self.dish,
            quantity=1,
            total_price="150.00",
            status=Order.Status.PLACED,
        )

        assigned_rider, _ = find_nearest_available_rider(new_order)

        self.assertEqual(assigned_rider, second_rider)

    def test_free_rider_can_claim_nearby_unassigned_order(self):
        self.login_rider()
        order = Order.objects.create(
            resident=self.resident,
            chef=self.chef,
            dish=self.dish,
            quantity=1,
            total_price="150.00",
            status=Order.Status.PLACED,
        )

        response = self.client.post(
            f"/rider/jobs/{order.id}/claim/",
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.rider, self.rider)
        self.assertEqual(order.status, Order.Status.ACCEPTED)

    def test_resident_notifications_include_rider_name_on_accept(self):
        order = Order.objects.create(
            resident=self.resident,
            chef=self.chef,
            dish=self.dish,
            rider=self.rider,
            quantity=1,
            total_price="150.00",
            status=Order.Status.ASSIGNED,
        )
        self.login_rider()

        response = self.client.post(
            f"/rider/jobs/{order.id}/accept/",
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        resident_notification = Notification.objects.filter(recipient=self.resident).latest("created_at")
        self.assertIn(self.rider.get_full_name() or self.rider.username, resident_notification.message)
