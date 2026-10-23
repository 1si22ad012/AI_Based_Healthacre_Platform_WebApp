from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import PatientProfile
from accounts.permissions import can_access_patient
from .models import MedicalRecord
from .serializers import MedicalRecordSerializer
from .services import encrypt_medical_record


class MedicalRecordListView(generics.ListAPIView):
    serializer_class = MedicalRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_patient():
            return MedicalRecord.objects.filter(patient=user.patient_profile, is_deleted=False).order_by("-created_at")
        if user.is_doctor():
            return MedicalRecord.objects.filter(created_by=user, is_deleted=False).order_by("-created_at")
        if user.is_superuser or getattr(user, "role", "") == "admin":
            return MedicalRecord.objects.filter(is_deleted=False).order_by("-created_at")
        return MedicalRecord.objects.none()


class CreateEncryptedRecordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        patient = PatientProfile.objects.filter(id=request.data.get("patient_id")).first()
        if not patient or not can_access_patient(request.user, patient):
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
        try:
            record, policy = encrypt_medical_record(
                request.user,
                patient,
                request.data.get("title", "Encrypted Record"),
                request.data.get("content", ""),
                request.data.get("sensitivity", "high"),
                request=request,
            )
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        return Response({"id": record.id, "policy": policy}, status=status.HTTP_201_CREATED)
