from django.test import Client
from django.test import TestCase

from .forms import SignupForm
from .models import User


class SignupFormTests(TestCase):
    def test_signup_form_rejects_invalid_phone_number(self):
        form = SignupForm(
            data={
                "full_name": "Nandini Sharma",
                "role": "resident",
                "phone_number": "12345",
                "vehicle_details": "",
                "location_name": "Palm Meadows",
                "latitude": "28.45",
                "longitude": "77.02",
                "email": "invalid-phone@example.com",
                "password": "Strong123",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("phone_number", form.errors)

    def test_signup_form_rejects_numeric_name(self):
        form = SignupForm(
            data={
                "full_name": "12345",
                "role": "resident",
                "phone_number": "9876543210",
                "vehicle_details": "",
                "location_name": "Palm Meadows",
                "latitude": "28.45",
                "longitude": "77.02",
                "email": "invalid-name@example.com",
                "password": "Strong123",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("full_name", form.errors)

    def test_rider_signup_requires_vehicle_details(self):
        form = SignupForm(
            data={
                "full_name": "Rider Demo",
                "role": "rider",
                "phone_number": "9876543210",
                "vehicle_details": "",
                "location_name": "Palm Meadows",
                "latitude": "28.45",
                "longitude": "77.02",
                "email": "rider@example.com",
                "password": "Strong123",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("vehicle_details", form.errors)


class AuthenticationFlowTests(TestCase):
    def test_signup_and_login_set_auth_cookie(self):
        client = Client()

        signup_response = client.post(
            "/signup/",
            {
                "full_name": "Resident Demo",
                "role": "resident",
                "phone_number": "9876543210",
                "vehicle_details": "",
                "location_name": "Palm Meadows",
                "latitude": "28.45",
                "longitude": "77.02",
                "email": "resident-auth@example.com",
                "password": "Strong123",
            },
            follow=True,
        )

        self.assertEqual(signup_response.status_code, 200)
        self.assertIn("auth_token", client.cookies)

        logout_response = client.post("/logout/", follow=True)
        self.assertEqual(logout_response.status_code, 200)
        self.assertEqual(client.cookies["auth_token"].value, "")

        login_response = client.post(
            "/",
            {
                "role": "resident",
                "username": "resident-auth@example.com",
                "password": "Strong123",
            },
            follow=True,
        )

        self.assertEqual(login_response.status_code, 200)
        self.assertIn("auth_token", client.cookies)
        self.assertContains(login_response, "Welcome")
