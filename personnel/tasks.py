# personnel/tasks.py

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Personnel, Document, Payment
from utils.email_service import EmailService
# Ensure the correct path to DocumentManager is used
# Ensure the correct path to DocumentManager is used
# from personnel.utils.document_manager import DocumentManager
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_daily_document_reminders():
    """Send document reminders to personnel with missing documents"""
    email_service = EmailService()
    
    # Get personnel with incomplete documents
    incomplete_personnel = Personnel.objects.filter(
        documents_complete=False,
        is_active=True
    )
    
    sent_count = 0
    for personnel in incomplete_personnel:
        missing_docs = personnel.get_missing_documents()
        if missing_docs:
            try:
                email_service.send_document_reminder(personnel)
                sent_count += 1
            except Exception as e:
                logger.error(f"Error sending reminder to {personnel.email}: {str(e)}")
    
    return f"Sent reminders to {sent_count} personnel"

@shared_task
def send_payment_reminders():
    """Send payment reminders to personnel with pending payments"""
    email_service = EmailService()
    
    # Get personnel with pending payments
    pending_payments = Payment.objects.filter(
        payment_status='pending'
    ).select_related('personnel')
    
    sent_count = 0
    for payment in pending_payments:
        try:
            email_service.send_payment_notification(payment.personnel)
            sent_count += 1
        except Exception as e:
            logger.error(f"Error sending payment reminder to {payment.personnel.email}: {str(e)}")
    
    return f"Sent payment reminders to {sent_count} personnel"

@shared_task
def check_expiring_documents():
    """Check for documents expiring within 30 days"""
    expiry_threshold = timezone.now().date() + timedelta(days=30)
    
    expiring_docs = Document.objects.filter(
        expiry_date__lte=expiry_threshold,
        expiry_date__gte=timezone.now().date(),
        is_complete=True
    ).select_related('personnel')
    
    notifications = []
    for doc in expiring_docs:
        notifications.append({
            'personnel': doc.personnel.full_name(),
            'document_type': doc.get_document_type_display(),
            'expiry_date': doc.expiry_date,
            'days_until_expiry': (doc.expiry_date - timezone.now().date()).days
        })
    
    # Log notifications
    if notifications:
        logger.info(f"Found {len(notifications)} documents expiring soon")
    
    return {
        'expiring_count': len(notifications),
        'details': notifications
    }

@shared_task
def auto_send_complete_profiles_to_finance():
    """Automatically send complete profiles to finance"""
    # Get complete profiles not yet sent to finance
    complete_personnel = Personnel.objects.filter(
        documents_complete=True,
        is_active=True,
        payments__payment_status='pending'
    ).distinct()
    
    sent_count = 0
    for personnel in complete_personnel:
        try:
            payment = Payment.objects.get(personnel=personnel)
            payment.payment_status = 'submitted_to_finance'
            payment.finance_submission_date = timezone.now()
            payment.save()
            
            # Send notification
            email_service = EmailService()
            email_service.send_finance_submission_notification(personnel)
            
            sent_count += 1
        except Payment.DoesNotExist:
            # No payment record found, create one
            from .utils.payment_calculator import PaymentCalculator
            calculator = PaymentCalculator(personnel)
            calculator.calculate_payment()
            
            # Send to finance
            payment = Payment.objects.get(personnel=personnel)
            payment.payment_status = 'submitted_to_finance'
            payment.finance_submission_date = timezone.now()
            payment.save()
            
            email_service = EmailService()
            email_service.send_finance_submission_notification(personnel)
            
            sent_count += 1
        except Exception as e:
            logger.error(f"Error sending {personnel.email} to finance: {str(e)}")
    
    return f"Sent {sent_count} profiles to finance"

@shared_task
def generate_payment_report():
    """Generate and save payment report"""
    from io import BytesIO
    import pandas as pd
    
    payments = Payment.objects.select_related('personnel').all()
    
    data = []
    for payment in payments:
        data.append({
            'Name': payment.personnel.full_name(),
            'Role': payment.get_role_type_display(),
            'Nationality': payment.personnel.nationality,
            'Daily Rate': float(payment.daily_rate),
            'Days Worked': payment.days_worked,
            'Base Payment': float(payment.total_base),
            'Travel Allowance': float(payment.travel_allowance),
            'Accommodation': float(payment.accommodation_allowance),
            'Per Diem': float(payment.per_diem),
            'Special Allowance': float(payment.special_allowance),
            'Subtotal': float(payment.subtotal),
            'Tax (5%)': float(payment.tax),
            'Total': float(payment.total_amount),
            'Currency': payment.currency,
            'Status': payment.get_payment_status_display()
        })
    
    df = pd.DataFrame(data)
    
    # Save to media
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Payment Report', index=False)
    
    # Save file
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage
    from django.conf import settings
    
    file_path = f'reports/payment_report_{timezone.now().strftime("%Y%m%d")}.xlsx'
    saved_path = default_storage.save(file_path, ContentFile(output.getvalue()))
    
    return {
        'status': 'success',
        'file_path': saved_path,
        'total_payments': len(data)
    }