from rest_framework import serializers

from .models import Diagnosis, MedicalRecord


class MedicalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = ["id", "patient", "title", "record_type", "sensitivity", "algorithm", "key_version", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class DiagnosisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnosis
        fields = ["id", "patient", "title", "algorithm", "key_version", "created_at", "updated_at"]
        read_only_fields = fields
