from rest_framework import serializers

from .models import EncryptionOperation, KeyMetadata


class EncryptionOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EncryptionOperation
        fields = "__all__"
        read_only_fields = ["id", "created_at"]


class KeyMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyMetadata
        fields = ["id", "key_id", "version", "algorithm", "status", "fingerprint", "created_at", "rotated_at"]
        read_only_fields = fields
