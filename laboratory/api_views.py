from rest_framework import generics, permissions

from .models import LabTestRequest, LabReport
from .serializers import LabReportSerializer, LabTestRequestSerializer


class LabRequestListCreateView(generics.ListCreateAPIView):
    queryset = LabTestRequest.objects.all().order_by("-created_at")
    serializer_class = LabTestRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_patient():
            return LabTestRequest.objects.filter(patient=user.patient_profile).order_by("-created_at")
        if user.is_doctor():
            return LabTestRequest.objects.filter(doctor=user).order_by("-created_at")
        if user.is_lab_tech():
            return LabTestRequest.objects.filter(assigned_technician=user).order_by("-created_at")
        if user.is_superuser or getattr(user, "role", "") == "admin":
            return LabTestRequest.objects.all().order_by("-created_at")
        return LabTestRequest.objects.none()


class LabReportListView(generics.ListAPIView):
    queryset = LabReport.objects.all().order_by("-created_at")
    serializer_class = LabReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_patient():
            return LabReport.objects.filter(request__patient=user.patient_profile).order_by("-created_at")
        if user.is_doctor():
            return LabReport.objects.filter(request__doctor=user).order_by("-created_at")
        if user.is_lab_tech():
            return LabReport.objects.filter(technician=user).order_by("-created_at")
        if user.is_superuser or getattr(user, "role", "") == "admin":
            return LabReport.objects.all().order_by("-created_at")
        return LabReport.objects.none()
