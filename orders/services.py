from decimal import Decimal

from accounts.models import User

from .models import Notification, Order


MAX_ASSIGNMENT_DISTANCE_KM = Decimal("2.0")


def approximate_distance_km(lat1, lng1, lat2, lng2):
    lat_gap = (Decimal(str(lat1)) - Decimal(str(lat2))) * Decimal("111")
    lng_gap = (Decimal(str(lng1)) - Decimal(str(lng2))) * Decimal("111")
    distance = (lat_gap * lat_gap + lng_gap * lng_gap).sqrt()
    return distance.quantize(Decimal("0.01"))


def find_nearest_available_rider(order):
    riders = User.objects.filter(
        role=User.Role.RIDER,
        is_available=True,
    )

    selected_rider = None
    selected_distance = None

    for rider in riders:
        busy = Order.objects.filter(rider=rider).exclude(status=Order.Status.DELIVERED).exists()
        if busy:
            continue

        distance = approximate_distance_km(
            order.chef.latitude,
            order.chef.longitude,
            rider.latitude,
            rider.longitude,
        )

        if distance > MAX_ASSIGNMENT_DISTANCE_KM:
            continue

        if selected_distance is None or distance < selected_distance:
            selected_rider = rider
            selected_distance = distance

    return selected_rider, selected_distance


def get_nearby_unassigned_orders_for_rider(rider):
    nearby_orders = []
    orders = Order.objects.filter(
        rider__isnull=True,
        status=Order.Status.PLACED,
    ).select_related("dish", "chef", "resident")

    for order in orders:
        distance = approximate_distance_km(
            order.chef.latitude,
            order.chef.longitude,
            rider.latitude,
            rider.longitude,
        )
        if distance <= MAX_ASSIGNMENT_DISTANCE_KM:
            nearby_orders.append((order, distance))

    nearby_orders.sort(key=lambda item: item[1])
    return nearby_orders


def create_notification(recipient, title, message, order=None):
    Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        order=order,
    )
