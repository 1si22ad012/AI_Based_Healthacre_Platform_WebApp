from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import EncryptionOperation, KeyMetadata
from .serializers import EncryptionOperationSerializer, KeyMetadataSerializer
from ai_security.services import select_policy


class EncryptionOperationListView(generics.ListAPIView):
    queryset = EncryptionOperation.objects.all().order_by("-created_at")
    serializer_class = EncryptionOperationSerializer
    permission_classes = [permissions.IsAuthenticated]


class KeyMetadataListView(generics.ListAPIView):
    queryset = KeyMetadata.objects.all().order_by("-created_at")
    serializer_class = KeyMetadataSerializer
    permission_classes = [permissions.IsAuthenticated]


class PolicyDecisionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        context = request.data or {}
        context.setdefault("role", request.user.role)
        decision = select_policy(context)
        return Response(decision)
