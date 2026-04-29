from django.test import TestCase
from apps.payouts.models import PayoutStatus
from apps.payouts.services import mark_processing, mark_completed, mark_failed

class PayoutStateMachineTests(TestCase):
    def test_completed_to_pending_is_rejected(self):
        
        pass

    def test_failed_refund_is_atomic(self):
       
        pass