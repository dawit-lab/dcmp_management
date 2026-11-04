# personnel/utils/account_service.py

import logging

from django.contrib.auth.models import User
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

from .tokens import make_response_token
from ..models import MeetingAssignment, CommunicationLog
from ..models import MeetingAssignment, CommunicationLog, UserProfile

logger = logging.getLogger(__name__)


class AccountService:
    """Create per-meeting user accounts and email credentials."""

    def __init__(self):
        self.default_from = settings.DEFAULT_FROM_EMAIL

    # ============================================================
    # ACCOUNT CREATION
    # ============================================================

    def create_account_for_personnel(self, personnel):
        """
        Create a User + MeetingAssignment for a personnel + meeting.
        Returns (assignment, plain_password) or raises ValueError.
        """
        if not personnel.meeting:
            raise ValueError("Personnel is not assigned to a meeting.")

        if MeetingAssignment.objects.filter(
            personnel=personnel, meeting=personnel.meeting
        ).exists():
            raise ValueError(
                f"An account already exists for {personnel.full_name()} "
                f"in '{personnel.meeting.name}'."
            )

        username = MeetingAssignment.generate_username(personnel, personnel.meeting)
        plain_password = MeetingAssignment.generate_password()

        user = User.objects.create_user(
            username=username,
            email=personnel.email,
            password=plain_password,
            first_name=personnel.first_name,
            last_name=personnel.last_name,
            is_staff=False,
            is_superuser=False,
            is_active=True,
        )

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.must_change_password = True
        profile.save()

        role = 'coordinator'
        if personnel.personnel_type == 'translator':
            role = 'translator'
        elif personnel.personnel_type == 'interpreter':
            role = 'interpreter'

        assignment = MeetingAssignment.objects.create(
            user=user,
            personnel=personnel,
            meeting=personnel.meeting,
            role=role,
            username_for_meeting=username,
            plain_password_hint=plain_password,
        )

        return assignment, plain_password

    # ============================================================
    # CREDENTIALS
    # ============================================================

    def send_credentials_email(self, assignment, admin_email=None):
        """
        Email the credentials to the personnel; CC the admin.
        Logs to CommunicationLog.
        """
        personnel = assignment.personnel
        meeting = assignment.meeting

        base = getattr(settings, 'API_BASE_URL', 'http://localhost:8000')
        # Strip trailing /api and trailing slash, then append /login/
        login_url = base.rstrip('/')
        if login_url.endswith('/api'):
            login_url = login_url[:-4]
        login_url = login_url.rstrip('/') + '/login/'

        subject = f"Your DCMP Access Credentials for {meeting.name}"
        context = {
            'personnel': personnel,
            'meeting': meeting,
            'username': assignment.username_for_meeting,
            'password': assignment.plain_password_hint,
            'login_url': login_url,
        }

        html = render_to_string('emails/credentials_email.html', context)
        text = strip_tags(html)

        to_list = [personnel.email]
        cc_list = [admin_email] if admin_email else []

        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text,
                from_email=self.default_from,
                to=to_list,
                cc=cc_list,
            )
            msg.attach_alternative(html, "text/html")
            msg.send()

            assignment.credentials_sent_at = timezone.now()
            assignment.plain_password_hint = ''
            assignment.save(update_fields=['credentials_sent_at', 'plain_password_hint'])

            CommunicationLog.objects.create(
                personnel=personnel,
                communication_type='general',
                subject=subject,
                content=text[:1000],
                recipient_email=personnel.email,
                status='sent',
                metadata={
                    'type': 'meeting_credentials',
                    'meeting_id': meeting.id,
                    'assignment_id': assignment.id,
                }
            )
            return True, None

        except Exception as e:
            logger.error(f"Failed to send credentials email: {e}", exc_info=True)
            CommunicationLog.objects.create(
                personnel=personnel,
                communication_type='general',
                subject=subject,
                content=text[:1000],
                recipient_email=personnel.email,
                status='failed',
                error_message=str(e),
            )
            return False, str(e)

    # ============================================================
    # DOCUMENT UPLOAD NOTIFICATION
    # ============================================================

    def send_upload_notification_to_admin(self, personnel, document):
        """Notify admin when personnel uploads a document; CC personnel."""
        subject = (
            f"Document Uploaded: {document.get_document_type_display()} — "
            f"{personnel.full_name()}"
        )
        context = {
            'personnel': personnel,
            'document': document,
            'meeting': personnel.meeting,
        }
        html = render_to_string('emails/upload_notification.html', context)
        text = strip_tags(html)

        admin_email = settings.DEFAULT_FROM_EMAIL
        if getattr(settings, 'ADMINS', None):
            admin_email = settings.ADMINS[0][1]

        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text,
                from_email=self.default_from,
                to=[admin_email],
                cc=[personnel.email],
            )
            msg.attach_alternative(html, "text/html")
            msg.send()

            CommunicationLog.objects.create(
                personnel=personnel,
                communication_type='completion_notification',
                subject=subject,
                content=text[:1000],
                recipient_email=admin_email,
                status='sent',
            )
            return True, None
        except Exception as e:
            logger.error(f"Failed to send upload notification: {e}", exc_info=True)
            return False, str(e)

    # ============================================================
    # AVAILABILITY WORKFLOW
    # ============================================================

    def send_availability_invitation(self, availability_request, request=None):
        """
        Send an availability invitation email with Yes/No links.
        """
        personnel = availability_request.personnel
        meeting = availability_request.meeting

        yes_token = make_response_token(availability_request.id, 'yes')
        no_token = make_response_token(availability_request.id, 'no')

        base_url = self._site_base_url(request)

        yes_url = f"{base_url}/availability/respond/{yes_token}/"
        no_url = f"{base_url}/availability/respond/{no_token}/"

        subject = f"Availability Request — {meeting.name}"
        context = {
            'personnel': personnel,
            'meeting': meeting,
            'yes_url': yes_url,
            'no_url': no_url,
        }

        html = render_to_string('emails/availability_invitation.html', context)
        text = strip_tags(html)

        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text,
                from_email=self.default_from,
                to=[personnel.email],
            )
            msg.attach_alternative(html, "text/html")
            msg.send()

            availability_request.invitation_sent_at = timezone.now()
            availability_request.save(update_fields=['invitation_sent_at'])

            CommunicationLog.objects.create(
                personnel=personnel,
                communication_type='general',
                subject=subject,
                content=text[:1000],
                recipient_email=personnel.email,
                status='sent',
                metadata={
                    'type': 'availability_invitation',
                    'meeting_id': meeting.id,
                    'availability_request_id': availability_request.id,
                }
            )
            return True, None
        except Exception as e:
            logger.error(f"Failed to send invitation: {e}", exc_info=True)
            CommunicationLog.objects.create(
                personnel=personnel,
                communication_type='general',
                subject=subject,
                content=text[:1000],
                recipient_email=personnel.email,
                status='failed',
                error_message=str(e),
            )
            return False, str(e)

    def send_availability_response_to_admin(self, availability_request):
        """Notify admin that a person responded."""
        personnel = availability_request.personnel
        meeting = availability_request.meeting
        status_display = availability_request.get_status_display()

        admin_email = self._admin_email()
        if not admin_email:
            return False, "No admin email configured"

        subject = f"Availability Response: {personnel.full_name()} — {status_display}"
        context = {
            'personnel': personnel,
            'meeting': meeting,
            'availability_request': availability_request,
        }
        html = render_to_string('emails/availability_response_admin.html', context)
        text = strip_tags(html)

        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text,
                from_email=self.default_from,
                to=[admin_email],
            )
            msg.attach_alternative(html, "text/html")
            msg.send()

            CommunicationLog.objects.create(
                personnel=personnel,
                communication_type='general',
                subject=subject,
                content=text[:1000],
                recipient_email=admin_email,
                status='sent',
                metadata={
                    'type': 'availability_response_admin',
                    'availability_request_id': availability_request.id,
                }
            )
            return True, None
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}", exc_info=True)
            return False, str(e)

    def send_approval_confirmation(self, availability_request):
        """Tell the person they've been approved and credentials are coming separately."""
        personnel = availability_request.personnel
        meeting = availability_request.meeting

        subject = f"You have been approved — {meeting.name}"
        context = {'personnel': personnel, 'meeting': meeting}
        html = render_to_string('emails/approval_confirmation.html', context)
        text = strip_tags(html)

        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text,
                from_email=self.default_from,
                to=[personnel.email],
            )
            msg.attach_alternative(html, "text/html")
            msg.send()
            return True, None
        except Exception as e:
            logger.error(f"Failed to send approval confirmation: {e}", exc_info=True)
            return False, str(e)

    def send_decline_acknowledgement(self, availability_request):
        """Thank the person for their response."""
        personnel = availability_request.personnel
        meeting = availability_request.meeting

        subject = f"Thank you for your response — {meeting.name}"
        context = {'personnel': personnel, 'meeting': meeting}
        html = render_to_string('emails/decline_acknowledgement.html', context)
        text = strip_tags(html)

        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text,
                from_email=self.default_from,
                to=[personnel.email],
            )
            msg.attach_alternative(html, "text/html")
            msg.send()
            return True, None
        except Exception as e:
            logger.error(f"Failed to send decline ack: {e}", exc_info=True)
            return False, str(e)

    def send_documents_complete_notification(self, personnel):
        """Notify admin + personnel that all documents are uploaded."""
        admin_email = self._admin_email()
        meeting = personnel.meeting

        subject = (
            f"Documents Complete: {personnel.full_name()} — "
            f"{meeting.name if meeting else 'N/A'}"
        )

        # To admin
        if admin_email:
            context = {'personnel': personnel, 'meeting': meeting, 'for_admin': True}
            html = render_to_string('emails/documents_complete.html', context)
            text = strip_tags(html)
            try:
                msg = EmailMultiAlternatives(
                    subject=subject, body=text,
                    from_email=self.default_from, to=[admin_email],
                )
                msg.attach_alternative(html, "text/html")
                msg.send()
            except Exception as e:
                logger.error(f"Admin notification failed: {e}", exc_info=True)

        # To personnel
        context = {'personnel': personnel, 'meeting': meeting, 'for_admin': False}
        html = render_to_string('emails/documents_complete.html', context)
        text = strip_tags(html)
        try:
            msg = EmailMultiAlternatives(
                subject=subject, body=text,
                from_email=self.default_from, to=[personnel.email],
            )
            msg.attach_alternative(html, "text/html")
            msg.send()
        except Exception as e:
            logger.error(f"Personnel notification failed: {e}", exc_info=True)

        return True, None

    # ============================================================
    # HELPERS
    # ============================================================

    def _site_base_url(self, request=None):
        """Build the base URL of the site (without /api)."""
        if request is not None:
            return request.build_absolute_uri('/').rstrip('/')
        base = getattr(settings, 'API_BASE_URL', 'http://localhost:8000')
        return base.rstrip('/').rsplit('/api', 1)[0] or base.rstrip('/')

    def _admin_email(self):
        """Return the admin notification email."""
        admins = getattr(settings, 'ADMINS', None)
        if admins:
            return admins[0][1]
        return getattr(settings, 'DEFAULT_FROM_EMAIL', None)