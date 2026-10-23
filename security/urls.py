from django.urls import path

from . import views

app_name = "security"

urlpatterns = [
    path("encryption-activity/", views.encryption_activity_view, name="encryption_activity"),
    path("key-management/", views.key_management_view, name="key_management"),
    path("key-management/rotate/", views.rotate_key_view, name="rotate_key"),
    path("policy-demo/", views.policy_demo_view, name="policy_demo"),
]
