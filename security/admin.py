from django.contrib import admin
from .models import KeyMetadata, EncryptedDocument, EncryptionOperation, SecurityPolicySetting

admin.site.register(KeyMetadata)
admin.site.register(EncryptedDocument)
admin.site.register(EncryptionOperation)
admin.site.register(SecurityPolicySetting)
