# from django.urls import path
# from .consumers import TripConsumer

# websocket_urlpatterns = [
#     path("ws/trip/", TripConsumer.as_asgi()),
# ]

from django.urls import re_path
from .consumers import TripConsumer

websocket_urlpatterns = [
    re_path(r'^ws/trip/$', TripConsumer.as_asgi()),
]