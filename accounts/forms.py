import re

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.text import slugify

from .models import User


def build_unique_username(full_name, email):
    base_name = slugify(full_name) or email.split("@")[0]
    username = base_name[:150] or "user"
    count = 1

    while User.objects.filter(username=username).exists():
        count += 1
        username = f"{base_name[:145]}-{count}"

    return username


class SignupForm(forms.ModelForm):
    full_name = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    phone_number = forms.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex=r"^\d{10}$",
                message="Phone number must contain exactly 10 digits.",
            )
        ],
    )

    class Meta:
        model = User
        fields = [
            "full_name",
            "role",
            "phone_number",
            "vehicle_details",
            "location_name",
            "latitude",
            "longitude",
            "email",
            "password",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        roles = []
        for value, label in User.Role.choices:
            if value != User.Role.ADMIN:
                roles.append((value, label))
        self.fields["role"].choices = roles

        self.fields["full_name"].widget.attrs.update(
            {"placeholder": "Enter your full name", "maxlength": "150"}
        )
        self.fields["role"].widget.attrs.update({"class": "role-select"})
        self.fields["phone_number"].widget.attrs.update(
            {
                "placeholder": "9876543210",
                "inputmode": "numeric",
                "maxlength": "10",
                "pattern": r"\d{10}",
            }
        )
        self.fields["vehicle_details"].widget.attrs.update(
            {
                "placeholder": "Bike - DL 01 AB 1234",
                "maxlength": "150",
            }
        )
        self.fields["location_name"].widget.attrs.update(
            {"placeholder": "Green Valley", "maxlength": "150"}
        )
        self.fields["latitude"].widget.attrs.update(
            {"placeholder": "28.459500", "step": "0.000001", "min": "-90", "max": "90"}
        )
        self.fields["longitude"].widget.attrs.update(
            {"placeholder": "77.026600", "step": "0.000001", "min": "-180", "max": "180"}
        )
        self.fields["email"].widget.attrs.update(
            {"placeholder": "you@example.com", "maxlength": "254"}
        )
        self.fields["password"].widget.attrs.update(
            {"placeholder": "Create a password", "minlength": "8"}
        )

    def clean_full_name(self):
        full_name = " ".join(self.cleaned_data["full_name"].split())
        if len(full_name) < 3:
            raise ValidationError("Full name must be at least 3 characters long.")
        if not re.fullmatch(r"[A-Za-z ]+", full_name):
            raise ValidationError("Full name should contain only letters and spaces.")
        return full_name

    def clean_phone_number(self):
        phone_number = self.cleaned_data["phone_number"].strip()
        if not re.fullmatch(r"\d{10}", phone_number):
            raise ValidationError("Phone number must contain exactly 10 digits.")
        return phone_number

    def clean_role(self):
        role = self.cleaned_data["role"]
        if role == User.Role.ADMIN:
            raise ValidationError("Admin accounts can only be created from the terminal.")
        return role

    def clean_vehicle_details(self):
        vehicle_details = " ".join(self.cleaned_data.get("vehicle_details", "").split())
        role = self.cleaned_data.get("role")

        if role == User.Role.RIDER and len(vehicle_details) < 3:
            raise ValidationError("Vehicle details are required for rider signup.")

        if vehicle_details and len(vehicle_details) < 3:
            raise ValidationError("Vehicle details must be at least 3 characters long.")

        return vehicle_details

    def clean_location_name(self):
        location_name = " ".join(self.cleaned_data["location_name"].split())
        if len(location_name) < 3:
            raise ValidationError("Location name must be at least 3 characters long.")
        if not re.fullmatch(r"[A-Za-z0-9 .,'-]+", location_name):
            raise ValidationError("Location name contains invalid characters.")
        return location_name

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean_password(self):
        password = self.cleaned_data["password"]
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
            raise ValidationError("Password must include at least one letter and one number.")
        return password

    def clean_latitude(self):
        latitude = self.cleaned_data["latitude"]
        if latitude < -90 or latitude > 90:
            raise ValidationError("Latitude must be between -90 and 90.")
        return latitude

    def clean_longitude(self):
        longitude = self.cleaned_data["longitude"]
        if longitude < -180 or longitude > 180:
            raise ValidationError("Longitude must be between -180 and 180.")
        return longitude

    def save(self, commit=True):
        user = super().save(commit=False)
        full_name = self.cleaned_data["full_name"].strip()
        parts = full_name.split(maxsplit=1)

        user.first_name = parts[0]
        user.last_name = parts[1] if len(parts) > 1 else ""
        user.username = build_unique_username(full_name, self.cleaned_data["email"])
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

        return user


class RoleLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={"placeholder": "you@example.com"}),
    )
    role = forms.ChoiceField(choices=User.Role.choices)

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        role = self.cleaned_data.get("role")
        if role and user.role != role:
            raise forms.ValidationError(
                "This account is registered under a different role.",
                code="invalid_role",
            )

    def clean(self):
        email = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        role = self.cleaned_data.get("role")

        if email and password:
            self.user_cache = authenticate(
                self.request,
                username=email,
                password=password,
            )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)

        if role and not email:
            raise forms.ValidationError("Enter your email address.", code="invalid_login")

        return self.cleaned_data
