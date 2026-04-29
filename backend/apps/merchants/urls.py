from django.urls import path
from .views import MerchantDashboardView

urlpatterns = [
    path("<uuid:merchant_id>/dashboard/", MerchantDashboardView.as_view()),
]