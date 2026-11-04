from rest_framework import serializers

from .models import ApprovalStatus, Role, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "role", "approval_status", "is_active", "date_joined"]
        read_only_fields = ["id", "date_joined", "approval_status", "is_active"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=10)
    role = serializers.ChoiceField(choices=[
        (Role.PATIENT, "Patient"),
        (Role.DOCTOR, "Doctor"),
        (Role.LAB_TECH, "Laboratory Technician"),
    ], default=Role.PATIENT)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "password", "role"]

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_role(self, value):
        if value not in {Role.PATIENT, Role.DOCTOR, Role.LAB_TECH}:
            raise serializers.ValidationError("Administrator registration is not allowed.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        role = validated_data.pop("role", Role.PATIENT)
        validated_data["role"] = role
        user = User(**validated_data)
        user.set_password(password)
        if role == Role.PATIENT:
            user.is_active = True
            user.approval_status = ApprovalStatus.APPROVED
        else:
            user.is_active = False
            user.approval_status = ApprovalStatus.PENDING
        user.save()
        from .models import DoctorProfile, LabTechProfile, PatientProfile

        if role == Role.PATIENT:
            PatientProfile.objects.get_or_create(user=user)
        elif role == Role.DOCTOR:
            DoctorProfile.objects.get_or_create(user=user)
        elif role == Role.LAB_TECH:
            LabTechProfile.objects.get_or_create(user=user)
        return user
