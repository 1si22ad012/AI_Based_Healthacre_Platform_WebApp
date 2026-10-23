from django.urls import path

from . import api_views

urlpatterns = [
    path("operations/", api_views.EncryptionOperationListView.as_view(), name="operations"),
    path("keys/", api_views.KeyMetadataListView.as_view(), name="keys"),
    path("policy-decision/", api_views.PolicyDecisionView.as_view(), name="policy-decision"),
]
