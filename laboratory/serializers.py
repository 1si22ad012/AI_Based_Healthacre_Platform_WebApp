from rest_framework import serializers

from .models import LabTestRequest, LabReport


class LabTestRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabTestRequest
        fields = ["id", "patient", "doctor", "assigned_technician", "test_type", "priority", "status", "notes", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class LabReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabReport
        fields = ["id", "request", "technician", "algorithm", "key_version", "status", "completed_at", "created_at", "updated_at"]
        read_only_fields = fields
