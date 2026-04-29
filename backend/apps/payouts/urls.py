from django.urls import path
from .views import CreatePayoutView, PayoutDetailView

urlpatterns = [
    path("", CreatePayoutView.as_view(), name="create-payout"),
    path("<uuid:payout_id>/", PayoutDetailView.as_view(), name="payout-detail"),
]