from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.models import AnomalyAlert, SecurityEvent
from audit.services import create_security_event
from .serializers import AnomalyAlertSerializer, SecurityEventSerializer
from .services import detect_anomaly, extract_security_features, persist_anomaly_detection


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
        features = extract_security_features(request.data or {})
        result = detect_anomaly(features)
        if result.get("is_anomaly"):
            detection = persist_anomaly_detection(features, result, actor=request.user, request=request, event_type="api_detect")
            result["detection_id"] = getattr(detection, "id", None)
        return Response(result, status=status.HTTP_200_OK)
