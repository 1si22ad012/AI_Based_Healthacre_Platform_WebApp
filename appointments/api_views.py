from rest_framework import generics, permissions

from .models import Appointment
from .serializers import AppointmentSerializer


class AppointmentListCreateView(generics.ListCreateAPIView):
    queryset = Appointment.objects.all().order_by("-scheduled_at")
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_patient():
            return Appointment.objects.filter(patient=user.patient_profile).order_by("-scheduled_at")
        if user.is_doctor():
            return Appointment.objects.filter(doctor=user).order_by("-scheduled_at")
        if user.is_superuser or getattr(user, "role", "") == "admin":
            return Appointment.objects.all().order_by("-scheduled_at")
        return Appointment.objects.none()
