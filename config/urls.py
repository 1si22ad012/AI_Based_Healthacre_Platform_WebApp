from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView



def healthz(request):
    return HttpResponse("ok", content_type="text/plain")

urlpatterns = [
    path("healthz/", healthz, name="healthz"),
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("patients/", include("patients.urls")),
    path("appointments/", include("appointments.urls")),
    path("prescriptions/", include("prescriptions.urls")),
    path("laboratory/", include("laboratory.urls")),
    path("security/", include("security.urls")),
    path("ai/", include("ai_security.urls")),
    path("audit/", include("audit.urls")),
    path("notifications/", include("notifications.urls")),
    path("api/", include("config.api_urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # Media files remain protected and are served through authorized views.
    pass
