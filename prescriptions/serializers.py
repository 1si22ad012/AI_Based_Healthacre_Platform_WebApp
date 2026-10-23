from rest_framework import serializers

from .models import Prescription, PrescriptionItem


class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = ["id", "patient", "doctor", "title", "status", "algorithm", "key_version", "signed_at", "created_at", "updated_at"]
        read_only_fields = fields


class PrescriptionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionItem
        fields = "__all__"
        read_only_fields = ["id", "created_at"]
