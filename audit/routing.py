from django.urls import re_path

from .consumers import SecurityAlertConsumer

websocket_urlpatterns = [
    re_path(r"ws/security/$", SecurityAlertConsumer.as_asgi()),
]
