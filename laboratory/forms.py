from django import forms


class LabRequestForm(forms.Form):
    patient_id = forms.IntegerField()
    test_type = forms.CharField(max_length=100)
    priority = forms.ChoiceField(choices=[("routine", "Routine"), ("urgent", "Urgent"), ("stat", "STAT")], initial="routine")
    notes = forms.CharField(widget=forms.Textarea, required=False)
    technician_id = forms.IntegerField(required=False)


class ReportUploadForm(forms.Form):
    request_id = forms.IntegerField()
    result_text = forms.CharField(widget=forms.Textarea, required=False)
    file = forms.FileField()
