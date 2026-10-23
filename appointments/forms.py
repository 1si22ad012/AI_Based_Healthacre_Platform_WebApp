from django import forms

from accounts.models import PatientProfile, User


class AppointmentForm(forms.Form):
    patient_id = forms.IntegerField()
    doctor_id = forms.IntegerField(required=False)
    scheduled_at = forms.DateTimeField()
    reason = forms.CharField(max_length=255, required=False)
    notes = forms.CharField(widget=forms.Textarea, required=False)
