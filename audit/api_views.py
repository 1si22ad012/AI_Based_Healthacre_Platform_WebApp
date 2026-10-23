from rest_framework import generics, permissions

from .models import AuditEvent
from .serializers import AuditEventSerializer


class AuditEventListView(generics.ListAPIView):
    serializer_class = AuditEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or getattr(user, "role", "") == "admin":
            return AuditEvent.objects.all().order_by("-created_at")
        return AuditEvent.objects.filter(actor=user).order_by("-created_at")
