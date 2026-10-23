from django.urls import include, path

urlpatterns = [
    path("auth/", include("accounts.api_urls")),
    path("patients/", include("patients.api_urls")),
    path("appointments/", include("appointments.api_urls")),
    path("prescriptions/", include("prescriptions.api_urls")),
    path("laboratory/", include("laboratory.api_urls")),
    path("security/", include("security.api_urls")),
    path("ai/", include("ai_security.api_urls")),
    path("audit/", include("audit.api_urls")),
    path("notifications/", include("notifications.api_urls")),
]
