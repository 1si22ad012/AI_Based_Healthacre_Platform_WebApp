from rest_framework import generics, permissions

from .models import Prescription
from .serializers import PrescriptionSerializer


class PrescriptionListView(generics.ListAPIView):
    queryset = Prescription.objects.all().order_by("-created_at")
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_patient():
            return Prescription.objects.filter(patient=user.patient_profile).order_by("-created_at")
        if user.is_doctor():
            return Prescription.objects.filter(doctor=user).order_by("-created_at")
        if user.is_superuser or getattr(user, "role", "") == "admin":
            return Prescription.objects.all().order_by("-created_at")
        return Prescription.objects.none()
