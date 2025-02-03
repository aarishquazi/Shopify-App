from .views import calculate_shipping
from django.urls import path

urlpatterns = [
    path("calculate-shipping/", calculate_shipping, name="calculate_shipping"),
]