from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from orders.models import Notification

from .forms import RoleLoginForm, SignupForm
from .jwt_utils import generate_jwt


ROLE_CARDS = [
    {
        "name": "HomeChef",
        "tagline": "Cook fresh meals from your kitchen and grow a trusted local food brand.",
        "emoji": "HomeChef",
    },
    {
        "name": "Resident",
        "tagline": "Discover nearby homemade food, order quickly, and track every meal live.",
        "emoji": "Resident",
    },
    {
        "name": "Rider",
        "tagline": "Pick up meals on time, deliver fast, and earn through flexible shifts.",
        "emoji": "Rider",
    },
]


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = RoleLoginForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        token = generate_jwt(user)
        response = redirect("dashboard")
        response.set_cookie(
            "auth_token",
            token,
            httponly=True,
            samesite="Lax",
            secure=False,
            max_age=60 * 60 * 24,
        )
        messages.success(request, "You are now logged in.")
        return response

    roles = [
        {
            "name": "Admin",
            "tagline": "Oversee users, listings, and orders from the platform control layer.",
            "emoji": "Admin",
        },
        *ROLE_CARDS,
    ]
    context = {
        "roles": roles,
        "form": form,
    }
    return render(request, "accounts/login.html", context)


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = SignupForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        token = generate_jwt(user)
        response = redirect("dashboard")
        response.set_cookie(
            "auth_token",
            token,
            httponly=True,
            samesite="Lax",
            secure=False,
            max_age=60 * 60 * 24,
        )
        messages.success(request, "Your account has been created.")
        return response

    context = {
        "roles": ROLE_CARDS,
        "form": form,
    }
    return render(request, "accounts/signup.html", context)


@login_required
def dashboard_view(request):
    notifications = Notification.objects.filter(recipient=request.user)[:6]
    context = {
        "notifications": notifications,
    }
    return render(request, "accounts/dashboard.html", context)


def logout_view(request):
    response = redirect("login")

    if request.method == "POST":
        logout(request)
        messages.success(request, "You have been logged out.")

    response.delete_cookie("auth_token")
    return response
