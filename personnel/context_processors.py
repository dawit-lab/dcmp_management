# personnel/context_processors.py
from .models import Personnel, Payment

def notification_count(request):
    """Add notification counts to all templates"""
    context = {}
    if request.user.is_authenticated:
        context['incomplete_count'] = Personnel.objects.filter(
            documents_complete=False, is_active=True
        ).count()
        context['pending_payments_count'] = Payment.objects.filter(
            payment_status='pending'
        ).count()
        context['submitted_payments_count'] = Payment.objects.filter(
            payment_status='submitted_to_finance'
        ).count()
    return context

from memos.models import Memo

def pending_memos_count(request):
    """Context processor to add pending memos count to all templates"""
    if request.user.is_authenticated:
        pending_count = Memo.objects.filter(
            is_completed=False
        ).count()
        return {'pending_memos_count': pending_count}
    return {'pending_memos_count': 0}