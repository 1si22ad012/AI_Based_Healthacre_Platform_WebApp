from django.contrib import admin
from .models import SecurityEvent, AnomalyAlert, AuditEvent

admin.site.register(SecurityEvent)
admin.site.register(AnomalyAlert)
admin.site.register(AuditEvent)
