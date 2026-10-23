from django.contrib import admin
from .models import LabTestRequest, LabReport

admin.site.register(LabTestRequest)
admin.site.register(LabReport)
