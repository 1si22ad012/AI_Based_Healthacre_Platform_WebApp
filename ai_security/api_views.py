from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.models import AnomalyAlert, SecurityEvent
from audit.services import create_security_event
from .serializers import AnomalyAlertSerializer, SecurityEventSerializer
from .services import detect_anomaly


class SecurityEventListView(generics.ListAPIView):
    queryset = SecurityEvent.objects.all().order_by("-created_at")
    serializer_class = SecurityEventSerializer
    permission_classes = [permissions.IsAuthenticated]


class AnomalyAlertListView(generics.ListAPIView):
    queryset = AnomalyAlert.objects.all().order_by("-created_at")
    serializer_class = AnomalyAlertSerializer
    permission_classes = [permissions.IsAuthenticated]


class DetectAnomalyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        result = detect_anomaly(request.data or {})
        if result.get("is_anomaly"):
            event = create_security_event("anomaly", actor=request.user, request=request, metadata=request.data or {}, severity="high", risk_score=result.get("score", 0.0))
            alert = AnomalyAlert.objects.create(security_event=event, detector="hybrid", score=result["score"], threshold=result["threshold"], status="open")
            result["alert_id"] = alert.id
        return Response(result, status=status.HTTP_200_OK)
