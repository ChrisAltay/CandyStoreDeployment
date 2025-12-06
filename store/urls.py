"""
URLs for store app
"""

from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("candy/<int:candy_id>/", views.candy_detail, name="candy_detail"),
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<int:candy_id>/", views.cart_add, name="cart_add"),
    path("cart/remove/<int:candy_id>/", views.cart_remove, name="cart_remove"),
]
