from decimal import Decimal
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from dishes.models import Dish

from .models import Notification, Order
from .services import create_notification, find_nearest_available_rider, get_nearby_unassigned_orders_for_rider


def resident_required(view_func):
    @wraps(view_func)
    def check_role(request, *args, **kwargs):
        if request.user.role != "resident":
            return HttpResponseForbidden("Only residents can access this page.")
        return view_func(request, *args, **kwargs)

    return check_role


def rider_required(view_func):
    @wraps(view_func)
    def check_role(request, *args, **kwargs):
        if request.user.role != "rider":
            return HttpResponseForbidden("Only riders can access this page.")
        return view_func(request, *args, **kwargs)

    return check_role


def get_cart(request):
    return request.session.setdefault("cart", {})


def save_cart(request, cart):
    request.session["cart"] = cart
    request.session.modified = True


def build_cart_items(request):
    cart = get_cart(request)
    items = []
    total = Decimal("0.00")

    for dish_id, quantity in cart.items():
        try:
            dish = Dish.objects.select_related("chef").get(
                id=int(dish_id),
                chef__role="chef",
                is_published=True,
            )
        except Dish.DoesNotExist:
            continue

        qty = int(quantity)
        item_total = dish.price * qty
        total += item_total
        items.append(
            {
                "dish": dish,
                "quantity": qty,
                "item_total": item_total,
            }
        )

    return items, total


def create_order_notifications(order, rider, distance):
    if rider:
        order.rider = rider
        order.status = Order.Status.ASSIGNED
        order.save(update_fields=["rider", "status", "updated_at"])

        rider_name = rider.get_full_name() or rider.username
        create_notification(
            order.resident,
            "Rider assigned",
            f"{rider_name} was assigned to your order for {order.dish.name}.",
            order,
        )
        create_notification(
            rider,
            "New assigned order",
            f"You were auto-assigned to pick up {order.dish.name}.",
            order,
        )
        create_notification(
            order.chef,
            "New order received",
            f"A resident ordered {order.quantity}x {order.dish.name}.",
            order,
        )
        return f"Order placed and assigned to the nearest rider within {distance} km."

    create_notification(
        order.resident,
        "Order placed",
        f"Your order for {order.dish.name} is waiting for a rider to claim it.",
        order,
    )
    create_notification(
        order.chef,
        "New order received",
        f"A resident ordered {order.quantity}x {order.dish.name}. Rider assignment is pending.",
        order,
    )
    return "Order placed successfully. No nearby rider was available within 2 km."


@login_required
@resident_required
def resident_feed_view(request):
    dishes = Dish.objects.filter(
        chef__role="chef",
        is_published=True,
        is_sold_out=False,
        quantity_available__gt=0,
    ).select_related("chef")

    current_orders = Order.objects.filter(resident=request.user).exclude(
        status=Order.Status.DELIVERED
    ).select_related("dish", "rider")[:5]

    past_orders = Order.objects.filter(
        resident=request.user,
        status=Order.Status.DELIVERED,
    ).select_related("dish", "rider")[:5]

    cart_items, cart_total = build_cart_items(request)
    notifications = Notification.objects.filter(recipient=request.user)[:5]

    context = {
        "dishes": dishes,
        "cart_items": cart_items,
        "cart_total": cart_total,
        "current_orders": current_orders,
        "past_orders": past_orders,
        "notifications": notifications,
    }
    return render(request, "orders/resident_feed.html", context)


@login_required
@resident_required
def add_to_cart_view(request, dish_id):
    if request.method != "POST":
        return redirect("resident-feed")

    dish = get_object_or_404(
        Dish,
        id=dish_id,
        chef__role="chef",
        is_published=True,
        is_sold_out=False,
        quantity_available__gt=0,
    )

    try:
        qty = int(request.POST.get("quantity", "1"))
    except ValueError:
        qty = 0

    if qty < 1:
        messages.error(request, "Quantity must be at least 1.")
        return redirect("resident-feed")

    cart = get_cart(request)
    old_qty = int(cart.get(str(dish.id), 0))
    new_qty = old_qty + qty

    if new_qty > dish.quantity_available:
        messages.error(request, "You cannot add more than the available quantity to the cart.")
        return redirect("resident-feed")

    cart[str(dish.id)] = new_qty
    save_cart(request, cart)
    messages.success(request, f"{dish.name} was added to your cart.")
    return redirect("resident-feed")


@login_required
@resident_required
def place_order_view(request, dish_id):
    if request.method != "POST":
        return redirect("resident-feed")

    dish = get_object_or_404(
        Dish,
        id=dish_id,
        chef__role="chef",
        is_published=True,
        is_sold_out=False,
    )

    try:
        qty = int(request.POST.get("quantity", "1"))
    except ValueError:
        qty = 0

    if qty < 1:
        messages.error(request, "Quantity must be at least 1.")
        return redirect("resident-feed")

    with transaction.atomic():
        current_dish = Dish.objects.select_for_update().get(id=dish.id)

        if current_dish.quantity_available < qty:
            messages.error(request, "Requested quantity is no longer available.")
            return redirect("resident-feed")

        current_dish.quantity_available -= qty
        if current_dish.quantity_available == 0:
            current_dish.is_sold_out = True
        current_dish.save(update_fields=["quantity_available", "is_sold_out", "updated_at"])

        order = Order.objects.create(
            resident=request.user,
            chef=current_dish.chef,
            dish=current_dish,
            quantity=qty,
            total_price=current_dish.price * qty,
            status=Order.Status.PLACED,
        )

        rider, distance = find_nearest_available_rider(order)
        message = create_order_notifications(order, rider, distance)

    messages.success(request, message)
    return redirect("resident-feed")


@login_required
@resident_required
def checkout_view(request):
    cart_items, total_amount = build_cart_items(request)

    if request.method == "POST":
        if not cart_items:
            messages.error(request, "Your cart is empty.")
            return redirect("resident-feed")

        billing_method = request.POST.get("billing_method")
        if billing_method != "cod":
            messages.error(request, "Only Cash on Delivery is available.")
            return redirect("resident-checkout")

        info_messages = []

        with transaction.atomic():
            for item in cart_items:
                dish = Dish.objects.select_for_update().get(id=item["dish"].id)
                qty = item["quantity"]

                if dish.is_sold_out or dish.quantity_available < qty:
                    messages.error(
                        request,
                        f"{dish.name} does not have enough quantity for checkout anymore.",
                    )
                    return redirect("resident-checkout")

                dish.quantity_available -= qty
                if dish.quantity_available == 0:
                    dish.is_sold_out = True
                dish.save(update_fields=["quantity_available", "is_sold_out", "updated_at"])

                order = Order.objects.create(
                    resident=request.user,
                    chef=dish.chef,
                    dish=dish,
                    quantity=qty,
                    total_price=dish.price * qty,
                    status=Order.Status.PLACED,
                )

                rider, distance = find_nearest_available_rider(order)
                info_messages.append(create_order_notifications(order, rider, distance))

        save_cart(request, {})
        messages.success(request, "Checkout completed with Cash on Delivery.")
        for message in info_messages:
            messages.info(request, message)
        return redirect("resident-orders")

    context = {
        "cart_items": cart_items,
        "total_amount": total_amount,
        "billing_method": "Cash on Delivery",
    }
    return render(request, "orders/checkout.html", context)


@login_required
@resident_required
def resident_orders_view(request):
    current_orders = Order.objects.filter(resident=request.user).exclude(
        status=Order.Status.DELIVERED
    ).select_related("dish", "chef", "rider")

    past_orders = Order.objects.filter(
        resident=request.user,
        status=Order.Status.DELIVERED,
    ).select_related("dish", "chef", "rider")

    notifications = Notification.objects.filter(recipient=request.user)[:8]
    context = {
        "current_orders": current_orders,
        "past_orders": past_orders,
        "notifications": notifications,
    }
    return render(request, "orders/resident_orders.html", context)


@login_required
@rider_required
def rider_jobs_view(request):
    orders = Order.objects.filter(rider=request.user).select_related("dish", "chef", "resident")
    active_order = orders.exclude(status=Order.Status.DELIVERED).first()
    nearby_orders = []

    if request.user.is_available and active_order is None:
        nearby_orders = get_nearby_unassigned_orders_for_rider(request.user)

    notifications = Notification.objects.filter(recipient=request.user)[:6]
    context = {
        "orders": orders,
        "active_order_id": active_order.id if active_order else None,
        "nearby_unassigned_orders": nearby_orders,
        "notifications": notifications,
    }
    return render(request, "orders/rider_jobs.html", context)


@login_required
@rider_required
def rider_toggle_availability_view(request):
    if request.method == "POST":
        request.user.is_available = not request.user.is_available
        request.user.save(update_fields=["is_available"])

        if request.user.is_available:
            messages.success(request, "You are now available for delivery jobs.")
        else:
            messages.success(request, "You are now offline.")

    return redirect("rider-jobs")


@login_required
@rider_required
def rider_claim_job_view(request, order_id):
    if request.method != "POST":
        return redirect("rider-jobs")

    busy = Order.objects.filter(rider=request.user).exclude(status=Order.Status.DELIVERED).exists()
    if busy:
        messages.error(request, "Deliver your current active order before claiming a new one.")
        return redirect("rider-jobs")

    if not request.user.is_available:
        messages.error(request, "Go online before claiming nearby orders.")
        return redirect("rider-jobs")

    with transaction.atomic():
        order = get_object_or_404(
            Order.objects.select_for_update().select_related("chef"),
            id=order_id,
            rider__isnull=True,
            status=Order.Status.PLACED,
        )

        nearby_orders = {}
        for near_order, distance in get_nearby_unassigned_orders_for_rider(request.user):
            nearby_orders[near_order.id] = distance

        distance = nearby_orders.get(order.id)
        if distance is None:
            messages.error(request, "This order is not within your nearby delivery range.")
            return redirect("rider-jobs")

        order.rider = request.user
        order.status = Order.Status.ACCEPTED
        order.save(update_fields=["rider", "status", "updated_at"])

        rider_name = request.user.get_full_name() or request.user.username
        create_notification(
            order.resident,
            "Rider claimed your order",
            f"{rider_name} claimed and accepted your order for {order.dish.name}.",
            order,
        )
        create_notification(
            order.chef,
            "Rider claimed order",
            f"{rider_name} claimed the order for {order.dish.name}.",
            order,
        )

    messages.success(request, f"You claimed this nearby job at {distance} km and accepted it.")
    return redirect("rider-jobs")


def update_rider_order_status(request, order_id, current_status, next_status, success_message):
    order = get_object_or_404(Order, id=order_id, rider=request.user)

    other_active = Order.objects.filter(rider=request.user).exclude(id=order.id).exclude(
        status=Order.Status.DELIVERED
    ).exists()
    if other_active:
        messages.error(
            request,
            "You already have another active order. Deliver it first before taking action on a new one.",
        )
        return redirect("rider-jobs")

    if order.status != current_status:
        messages.error(request, "This order is not ready for that action yet.")
        return redirect("rider-jobs")

    order.status = next_status
    order.save(update_fields=["status", "updated_at"])

    rider_name = order.rider.get_full_name() or order.rider.username
    resident_message = {
        Order.Status.ACCEPTED: f"{rider_name} accepted your order for {order.dish.name}.",
        Order.Status.PICKED_UP: f"{rider_name} picked up your order for {order.dish.name}.",
        Order.Status.DELIVERED: f"{rider_name} delivered your order for {order.dish.name}.",
    }
    chef_message = {
        Order.Status.ACCEPTED: f"The rider accepted delivery for {order.dish.name}.",
        Order.Status.PICKED_UP: f"{order.dish.name} has been picked up by the rider.",
        Order.Status.DELIVERED: f"{order.dish.name} was delivered to the resident.",
    }

    if next_status in resident_message:
        create_notification(order.resident, "Order update", resident_message[next_status], order)

    if next_status in chef_message:
        create_notification(order.chef, "Order update", chef_message[next_status], order)

    messages.success(request, success_message)
    return redirect("rider-jobs")


@login_required
@rider_required
def rider_accept_job_view(request, order_id):
    if request.method == "POST":
        return update_rider_order_status(
            request,
            order_id,
            Order.Status.ASSIGNED,
            Order.Status.ACCEPTED,
            "Delivery job accepted.",
        )
    return redirect("rider-jobs")


@login_required
@rider_required
def rider_pickup_job_view(request, order_id):
    if request.method == "POST":
        return update_rider_order_status(
            request,
            order_id,
            Order.Status.ACCEPTED,
            Order.Status.PICKED_UP,
            "Order marked as picked up.",
        )
    return redirect("rider-jobs")


@login_required
@rider_required
def rider_deliver_job_view(request, order_id):
    if request.method == "POST":
        return update_rider_order_status(
            request,
            order_id,
            Order.Status.PICKED_UP,
            Order.Status.DELIVERED,
            "Order marked as delivered.",
        )
    return redirect("rider-jobs")
