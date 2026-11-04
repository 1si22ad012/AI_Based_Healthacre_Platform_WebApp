from django.contrib import admin

from .models import AIConversation, FaceVerificationRecord, LoginAudit, SecurityIncident, SymptomAssessment

admin.site.register(AIConversation)
admin.site.register(FaceVerificationRecord)
admin.site.register(LoginAudit)
admin.site.register(SecurityIncident)
admin.site.register(SymptomAssessment)
