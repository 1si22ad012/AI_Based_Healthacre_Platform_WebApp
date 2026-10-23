from django import forms

from accounts.models import PatientProfile
from .models import MedicalRecord, Sensitivity


class MedicalRecordForm(forms.Form):
    patient_id = forms.IntegerField()
    title = forms.CharField(max_length=200)
    content = forms.CharField(widget=forms.Textarea)
    sensitivity = forms.ChoiceField(choices=Sensitivity.choices, initial=Sensitivity.HIGH)


class DiagnosisForm(forms.Form):
    patient_id = forms.IntegerField()
    title = forms.CharField(max_length=200)
    notes = forms.CharField(widget=forms.Textarea)
