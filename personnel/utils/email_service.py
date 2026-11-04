# personnel/utils/email_service.py

# personnel/utils/email_service.py - Update with detailed logging

import logging
from django.core.mail import send_mail, EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.conf import settings
from ..models import CommunicationLog

logger = logging.getLogger(__name__)

class EmailService:
    
    def __init__(self):
        self.default_from = settings.DEFAULT_FROM_EMAIL
    
    # def send_document_reminder(self, personnel):
    #     """Send document reminder email."""
    #     try:
    #         missing_docs = personnel.get_missing_documents()
    #         if not missing_docs:
    #             return {'status': 'error', 'message': 'No missing documents'}

    #         base = getattr(settings, 'API_BASE_URL', 'http://localhost:8000').rstrip('/')
    #         first_missing = missing_docs[0]

    #         # Pick the URL that matches the recipient:
    #         # - If the personnel has login credentials → self-service
    #         # - Otherwise → admin personnel detail page
    #         has_login = hasattr(personnel, 'meeting_assignments') and \
    #                     personnel.meeting_assignments.filter(is_active=True).exists()

    #         if has_login:
    #             upload_url = f"{base}/my-meeting/upload/{first_missing}/"
    #         else:
    #             upload_url = f"{base}/personnel/{personnel.id}/detail/"

    #         subject = f"ACTION REQUIRED: Missing Documents - {personnel.full_name()}"
    #         context = {
    #             'personnel': personnel,
    #             'missing_docs': missing_docs,
    #             'upload_link': upload_url,
    #         }

    #         html_content = render_to_string('emails/document_reminder.html', context)
    #         text_content = strip_tags(html_content)

    #         return self.send_email(
    #             recipient=personnel.email,
    #             subject=subject,
    #             html_content=html_content,
    #             text_content=text_content,
    #             communication_type='document_reminder',
    #             personnel=personnel,
    #         )
    #     except Exception as e:
    #         logger.error(f"Error in send_document_reminder: {e}", exc_info=True)
    #         return {'status': 'error', 'message': f'Error: {str(e)}'}
    
    def send_document_reminder(self, personnel):
        """Send document reminder email"""
        try:
            missing_docs = personnel.get_missing_documents()
            
            if not missing_docs:
                return {'status': 'error', 'message': 'No missing documents'}
            
            subject = f"ACTION REQUIRED: Missing Documents - {personnel.full_name()}"
            context = {
                'personnel': personnel,
                'missing_docs': missing_docs,
                'upload_link': f"{getattr(settings, 'API_BASE_URL', 'http://localhost:8000')}/documents/upload/"
            }
            
            html_content = render_to_string('emails/document_reminder.html', context)
            text_content = strip_tags(html_content)
            
            return self.send_email(
                recipient=personnel.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                communication_type='document_reminder',
                personnel=personnel
            )
        except Exception as e:
            logger.error(f"Error in send_document_reminder: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Error: {str(e)}'
            }
    
    def send_email(self, recipient, subject, html_content, text_content, 
                   communication_type, personnel, from_email=None):
        """Send email and log communication"""
        try:
            logger.info(f"=== EMAIL SENDING STARTED ===")
            logger.info(f"To: {recipient}")
            logger.info(f"From: {from_email or self.default_from}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Backend: {settings.EMAIL_BACKEND}")
            logger.info(f"Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
            logger.info(f"User: {settings.EMAIL_HOST_USER}")
            logger.info(f"TLS: {settings.EMAIL_USE_TLS}")
            logger.info(f"Password set: {bool(settings.EMAIL_HOST_PASSWORD)}")
            
            # Create email message
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email or self.default_from,
                to=[recipient]
            )
            msg.attach_alternative(html_content, "text/html")
            
            # Try to send
            logger.info("Attempting to send email via SMTP...")
            result = msg.send()
            
            logger.info(f"=== EMAIL SENT ===")
            logger.info(f"Result: {result}")
            
            # Log communication
            communication = CommunicationLog.objects.create(
                personnel=personnel,
                communication_type=communication_type,
                subject=subject,
                content=html_content[:1000],
                recipient_email=recipient,
                status='sent'
            )
            
            return {
                'status': 'success',
                'message': 'Email sent successfully',
                'communication_id': communication.id
            }
            
        except Exception as e:
            logger.error(f"=== EMAIL FAILED ===", exc_info=True)
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            return {
                'status': 'error',
                'message': f'Email sending failed: {str(e)}'
            }
        
    from django.utils import timezone  # add this import at the top if missing

    def send_finance_submission_notification(self, personnel):
        """Notify the personnel that their documents have been sent to Finance."""
        try:
            subject = f"Your documents have been submitted to Finance — {personnel.full_name()}"

            context = {
                'personnel': personnel,
                'meeting': personnel.meeting,
                'now': timezone.now(),
            }

            html_content = render_to_string('emails/finance_submission.html', context)
            text_content = strip_tags(html_content)

            return self.send_email(
                recipient=personnel.email,          # ← personnel, not admin
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                communication_type='finance_submission',
                personnel=personnel,
            )
        except Exception as e:
            logger.error(
                f"Error in send_finance_submission_notification: {e}", exc_info=True
            )
            return {'status': 'error', 'message': str(e)}
# import logging
# from django.core.mail import send_mail
# from django.template.loader import render_to_string
# from django.utils.html import strip_tags
# from django.conf import settings
# from ..models import CommunicationLog

# logger = logging.getLogger(__name__)

# class EmailService:
#     """Minimal email service – extend as needed."""
    
#     def __init__(self):
#         self.default_from = settings.DEFAULT_FROM_EMAIL
    
#     def send_document_reminder(self, personnel):
#         """Send document reminder (stub for now)."""
#         missing_docs = personnel.get_missing_documents()
#         if not missing_docs:
#             return {'status': 'error', 'message': 'No missing documents'}
        
#         subject = f"⚠️ Missing Documents - {personnel.full_name()}"
#         # For now, just log and return success (you can implement actual email later)
#         logger.info(f"Reminder email would be sent to {personnel.email} about missing docs.")
#         return {'status': 'success', 'message': 'Reminder sent (stub)'}
    
#     def send_completion_notification(self, personnel):
#         """Send completion notification (stub)."""
#         logger.info(f"Completion email would be sent to {personnel.email}.")
#         return {'status': 'success', 'message': 'Completion notification sent (stub)'}
    
#     def send_finance_submission_notification(self, personnel):
#         """Send finance submission notification (stub)."""
#         logger.info(f"Finance submission email would be sent to {personnel.email}.")
#         return {'status': 'success', 'message': 'Finance submission sent (stub)'}
    
#     def send_payment_notification(self, personnel):
#         """Send payment notification (stub)."""
#         logger.info(f"Payment email would be sent to {personnel.email}.")
#         return {'status': 'success', 'message': 'Payment notification sent (stub)'}

# # personnel/utils/email_service.py
# import logging
# from django.core.mail import send_mail
# from django.template.loader import render_to_string
# from django.utils.html import strip_tags
# from django.conf import settings
# from ..models import CommunicationLog

# logger = logging.getLogger(__name__)

# class EmailService:
#     """Minimal email service – extend as needed."""
    
#     def __init__(self):
#         self.default_from = settings.DEFAULT_FROM_EMAIL
    
#     def send_document_reminder(self, personnel):
#         """Send document reminder (stub for now)."""
#         missing_docs = personnel.get_missing_documents()
#         if not missing_docs:
#             return {'status': 'error', 'message': 'No missing documents'}
        
#         subject = f"⚠️ Missing Documents - {personnel.full_name()}"
#         # For now, just log and return success (you can implement actual email later)
#         logger.info(f"Reminder email would be sent to {personnel.email} about missing docs.")
#         return {'status': 'success', 'message': 'Reminder sent (stub)'}
    
#     def send_completion_notification(self, personnel):
#         """Send completion notification (stub)."""
#         logger.info(f"Completion email would be sent to {personnel.email}.")
#         return {'status': 'success', 'message': 'Completion notification sent (stub)'}
    
#     def send_finance_submission_notification(self, personnel):
#         """Send finance submission notification (stub)."""
#         logger.info(f"Finance submission email would be sent to {personnel.email}.")
#         return {'status': 'success', 'message': 'Finance submission sent (stub)'}
    
#     def send_payment_notification(self, personnel):
#         """Send payment notification (stub)."""
#         logger.info(f"Payment email would be sent to {personnel.email}.")
#         return {'status': 'success', 'message': 'Payment notification sent (stub)'}