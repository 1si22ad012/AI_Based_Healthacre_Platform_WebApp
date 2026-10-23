from django.urls import path

from . import views

app_name = "prescriptions"

urlpatterns = [
    path("", views.prescriptions_view, name="list"),
    path("create/", views.create_prescription_view, name="create"),
    path("<int:prescription_id>/", views.view_prescription_view, name="view"),
]
