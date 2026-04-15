from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from orders.models import Order

from .forms import DishForm
from .models import Dish
from .services import estimate_dish_nutrition_with_fallback


def chef_required(view_func):
    @wraps(view_func)
    def check_role(request, *args, **kwargs):
        if request.user.role != "chef":
            return HttpResponseForbidden("Only chefs can access this page.")
        return view_func(request, *args, **kwargs)

    return check_role


@login_required
@chef_required
def chef_dishes_view(request):
    form = DishForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        dish = form.save(commit=False)
        dish.chef = request.user

        nutrition = estimate_dish_nutrition_with_fallback(
            dish.name,
            dish.description,
            dish.media,
            dish.main_ingredient_amount,
        )
        dish.estimated_calories = nutrition["estimated_calories"]
        dish.health_score = nutrition["health_score"]
        dish.nutrition_notes = nutrition["nutrition_notes"]
        dish.is_veg = nutrition["is_veg"]
        dish.is_keto = nutrition["is_keto"]
        dish.is_high_protein = nutrition["is_high_protein"]
        dish.is_low_calorie = nutrition["is_low_calorie"]
        dish.save()
        messages.success(request, "Dish saved with nutrition estimates.")
        return redirect("chef-dishes")

    dishes = Dish.objects.filter(
        chef=request.user,
        quantity_available__gt=0,
        is_sold_out=False,
    )
    current_orders = Order.objects.filter(chef=request.user).exclude(
        status=Order.Status.DELIVERED
    ).select_related("dish", "resident", "rider")[:8]
    context = {
        "form": form,
        "dishes": dishes,
        "current_orders": current_orders,
    }
    return render(request, "dishes/chef_dishes.html", context)


@login_required
@chef_required
def mark_dish_sold_out_view(request, dish_id):
    if request.method == "POST":
        dish = get_object_or_404(Dish, id=dish_id, chef=request.user)
        dish.is_sold_out = True
        dish.quantity_available = 0
        dish.save(update_fields=["is_sold_out", "quantity_available", "updated_at"])
        messages.success(request, "Dish marked as sold out.")

    return redirect("chef-dishes")
