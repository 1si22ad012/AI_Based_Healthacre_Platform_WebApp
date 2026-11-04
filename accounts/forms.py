from django import forms
from django.contrib.auth import get_user_model

from .models import ApprovalStatus, Role

User = get_user_model()


class RegistrationForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, min_length=10)
    password2 = forms.CharField(widget=forms.PasswordInput, min_length=10)
    role = forms.ChoiceField(choices=[
        (Role.PATIENT, "Patient"),
        (Role.DOCTOR, "Doctor"),
        (Role.LAB_TECH, "Laboratory Technician"),
    ], initial=Role.PATIENT)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "role"]

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_role(self):
        role = self.cleaned_data["role"]
        if role not in {Role.PATIENT, Role.DOCTOR, Role.LAB_TECH}:
            raise forms.ValidationError("Invalid registration role.")
        return role

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        role = self.cleaned_data["role"]
        user.role = role
        user.set_password(self.cleaned_data["password1"])
        if role == Role.PATIENT:
            user.is_active = True
            user.approval_status = ApprovalStatus.APPROVED
        else:
            user.is_active = False
            user.approval_status = ApprovalStatus.PENDING
        if commit:
            user.save()
            from .models import DoctorProfile, LabTechProfile, PatientProfile

            if role == Role.PATIENT:
                PatientProfile.objects.get_or_create(user=user)
            elif role == Role.DOCTOR:
                DoctorProfile.objects.get_or_create(user=user)
            elif role == Role.LAB_TECH:
                LabTechProfile.objects.get_or_create(user=user)
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name"]


class AdminUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "role", "is_active"]
