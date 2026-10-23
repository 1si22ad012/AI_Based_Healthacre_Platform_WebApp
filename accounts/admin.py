from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, PatientProfile, DoctorProfile, LabTechProfile

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("email", "role", "is_active", "is_staff", "date_joined")
    ordering = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "first_name", "last_name", "role", "password1", "password2")}),
    )

admin.site.register(PatientProfile)
admin.site.register(DoctorProfile)
admin.site.register(LabTechProfile)
