from django import forms


class PrescriptionForm(forms.Form):
    patient_id = forms.IntegerField()
    title = forms.CharField(max_length=200)
    medication_name = forms.CharField(max_length=200)
    dosage = forms.CharField(max_length=100)
    frequency = forms.CharField(max_length=100)
    duration = forms.CharField(max_length=100, required=False)
    instructions = forms.CharField(widget=forms.Textarea, required=False)
    clinical_notes = forms.CharField(widget=forms.Textarea, required=False)
