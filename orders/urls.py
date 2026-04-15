from django.urls import path

from .views import (
    add_to_cart_view,
    chef_verify_pickup_view,
    checkout_view,
    place_order_view,
    resident_feed_view,
    resident_orders_view,
    rider_accept_job_view,
    rider_claim_job_view,
    rider_deliver_job_view,
    rider_jobs_view,
    rider_pickup_job_view,
    rider_toggle_availability_view,
)

urlpatterns = [
    path("resident/feed/", resident_feed_view, name="resident-feed"),
    path("resident/cart/add/<int:dish_id>/", add_to_cart_view, name="add-to-cart"),
    path("resident/checkout/", checkout_view, name="resident-checkout"),
    path("resident/orders/", resident_orders_view, name="resident-orders"),
    path("resident/dishes/<int:dish_id>/order/", place_order_view, name="place-order"),
    path("chef/orders/<int:order_id>/verify-pickup/", chef_verify_pickup_view, name="chef-verify-pickup"),
    path("rider/jobs/", rider_jobs_view, name="rider-jobs"),
    path("rider/toggle-availability/", rider_toggle_availability_view, name="rider-toggle-availability"),
    path("rider/jobs/<int:order_id>/claim/", rider_claim_job_view, name="rider-claim-job"),
    path("rider/jobs/<int:order_id>/accept/", rider_accept_job_view, name="rider-accept-job"),
    path("rider/jobs/<int:order_id>/pickup/", rider_pickup_job_view, name="rider-pickup-job"),
    path("rider/jobs/<int:order_id>/deliver/", rider_deliver_job_view, name="rider-deliver-job"),
]
