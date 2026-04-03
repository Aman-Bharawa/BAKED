from django.urls import path

from .views import chef_dishes_view, mark_dish_sold_out_view

urlpatterns = [
    path("chef/dishes/", chef_dishes_view, name="chef-dishes"),
    path("chef/dishes/<int:dish_id>/sold-out/", mark_dish_sold_out_view, name="dish-sold-out"),
]
