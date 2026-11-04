# personnel/views.py

import os
import io
import zipfile
import logging
import json
import pandas as pd
from decimal import Decimal
from datetime import datetime

from django.shortcuts import render, get_object_or_404, redirect
from django import forms
from django.http import FileResponse, HttpResponse, JsonResponse
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.signing import BadSignature, SignatureExpired
from django.http import HttpResponseForbidden

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny

from .models import (
    Personnel, Document, Payment, Meeting,
    CommunicationLog, NotificationTemplate,
    DocumentMerge, MergedDocument, PaymentSetting,
    AvailabilityRequest, MeetingAssignment, UserProfile,
    ContactMessage,
)
from .serializers import (
    PersonnelSerializer, DocumentSerializer, PaymentSerializer,
    MeetingSerializer, CommunicationLogSerializer, PersonnelExpenseSerializer,
)
from .utils.payment_calculator import PaymentCalculator
from .utils.email_service import EmailService
from .utils.document_merger import DocumentMerger
from .utils.account_service import AccountService
from .utils.tokens import parse_response_token
from .forms import PersonnelForm, DocumentUploadForm, MeetingForm, ContactForm

logger = logging.getLogger(__name__)


# ============================================================
# HOME
# ============================================================

def home(request):
    return render(request, 'personnel/home.html')


# ============================================================
# DRF VIEWSETS
# ============================================================

class PersonnelViewSet(viewsets.ModelViewSet):
    queryset = Personnel.objects.all()
    serializer_class = PersonnelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        # New-style filters
        profession = self.request.query_params.get('profession')
        if profession:
            queryset = queryset.filter(profession=profession)

        employment_basis = self.request.query_params.get('employment_basis')
        if employment_basis:
            queryset = queryset.filter(employment_basis=employment_basis)

        # Legacy filter — still supported for backward compatibility
        personnel_type = self.request.query_params.get('type')
        if personnel_type:
            queryset = queryset.filter(personnel_type=personnel_type)

        doc_status = self.request.query_params.get('doc_status')
        if doc_status == 'complete':
            queryset = queryset.filter(documents_complete=True)
        elif doc_status == 'incomplete':
            queryset = queryset.filter(documents_complete=False)

        meeting = self.request.query_params.get('meeting')
        if meeting:
            queryset = queryset.filter(meeting__id=meeting)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(nationality__icontains=search)
            )

        return queryset

    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        personnel = self.get_object()
        serializer = DocumentSerializer(personnel.documents.all(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def document_status(self, request, pk=None):
        personnel = self.get_object()
        context_name = request.query_params.get('context', 'routine')
        status = personnel.get_document_status(context=context_name)
        missing = personnel.get_missing_documents(context=context_name)
        return Response({
            'document_status': status,
            'missing_documents': missing,
            'is_complete': len(missing) == 0,
        })

    @action(detail=True, methods=['post'])
    def send_reminder(self, request, pk=None):
        personnel = self.get_object()
        email_service = EmailService()
        result = email_service.send_document_reminder(personnel)
        return Response(result)


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()
        personnel = serializer.instance.personnel
        if personnel.has_all_documents():
            personnel.documents_complete = True
            personnel.save(update_fields=['documents_complete'])
            EmailService().send_completion_notification(personnel)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        document = self.get_object()
        return FileResponse(
            document.file.open('rb'),
            as_attachment=True,
            filename=document.file_name,
        )

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        document = self.get_object()
        document.is_verified = True
        document.verified_by = request.user
        document.verification_date = timezone.now()
        document.verification_notes = request.data.get('notes', '')
        document.save()
        return Response({'message': 'Document verified successfully'})


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        status_ = self.request.query_params.get('status')
        if status_:
            queryset = queryset.filter(payment_status=status_)
        purpose = self.request.query_params.get('purpose')
        if purpose:
            queryset = queryset.filter(purpose=purpose)
        return queryset

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        payment = self.get_object()
        payment.payment_status = 'approved'
        payment.processed_by = request.user
        payment.save()
        EmailService().send_payment_notification(payment.personnel)
        return Response({'message': 'Payment approved successfully'})

    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        payment = self.get_object()
        payment.payment_status = 'paid'
        payment.payment_date = timezone.now()
        payment.payment_reference = request.data.get('reference', '')
        payment.processed_by = request.user
        payment.save()
        return Response({'message': 'Payment marked as paid'})


class MeetingViewSet(viewsets.ModelViewSet):
    queryset = Meeting.objects.all()
    serializer_class = MeetingSerializer
    permission_classes = [IsAuthenticated]


class CommunicationViewSet(viewsets.ModelViewSet):
    queryset = CommunicationLog.objects.all()
    serializer_class = CommunicationLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        personnel = self.request.query_params.get('personnel')
        if personnel:
            queryset = queryset.filter(personnel__id=personnel)
        return queryset


# ============================================================
# CUSTOM API VIEWS
# ============================================================

@api_view(['POST'])
@permission_classes([IsAdminUser])
def bulk_upload_personnel(request):
    """Bulk upload personnel from Excel."""
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

    file = request.FILES['file']
    try:
        df = pd.read_excel(file)
        created_count = 0
        errors = []

        for idx, row in df.iterrows():
            try:
                designation = str(row.get('Designation/Assigment', '')).lower()
                if 'interpreter' in designation:
                    profession = 'interpreter'
                elif 'translator' in designation:
                    profession = 'translator'
                else:
                    profession = 'other'

                Personnel.objects.create(
                    first_name=row.get('First Name', ''),
                    last_name=row.get('Last Name', ''),
                    nationality=row.get('Nationality', ''),
                    designation=row.get('Designation/Assigment', ''),
                    city_departure=row.get('City of Departure', ''),
                    profession=profession,
                    employment_basis='na',
                    payment_method='per_meeting',
                    personnel_type=profession,  # keep legacy field in sync
                    created_by=request.user,
                )
                created_count += 1
            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")

        return Response({
            'message': f'Successfully imported {created_count} personnel',
            'errors': errors,
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_document_api(request):
    """Upload document for personnel."""
    personnel_id = request.data.get('personnel_id')
    document_type = request.data.get('document_type')
    file = request.FILES.get('file')

    if not all([personnel_id, document_type, file]):
        return Response(
            {'error': 'personnel_id, document_type, and file are required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        personnel = Personnel.objects.get(id=personnel_id)
        document = Document.objects.create(
            personnel=personnel,
            document_type=document_type,
            file=file,
            notes=request.data.get('notes', ''),
        )
        serializer = DocumentSerializer(document)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Personnel.DoesNotExist:
        return Response({'error': 'Personnel not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_personnel_documents(request, pk):
    """Get all documents for a personnel."""
    try:
        personnel = Personnel.objects.get(id=pk)
        serializer = DocumentSerializer(personnel.documents.all(), many=True)
        return Response(serializer.data)
    except Personnel.DoesNotExist:
        return Response({'error': 'Personnel not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_document_reminder(request, pk):
    """Send document reminder to personnel."""
    try:
        logger.info(f"=== SEND REMINDER CALLED for personnel ID: {pk} ===")
        personnel = get_object_or_404(Personnel, id=pk)
        logger.info(f"Personnel found: {personnel.full_name()} ({personnel.email})")

        # Uses the new context-aware requirements
        missing_docs = personnel.get_missing_documents(context='routine')
        logger.info(f"Missing documents (routine): {missing_docs}")

        if not missing_docs:
            return Response({
                'status': 'error',
                'message': 'No missing documents for this personnel',
            }, status=status.HTTP_400_BAD_REQUEST)

        email_service = EmailService()
        result = email_service.send_document_reminder(personnel)
        logger.info(f"Email service result: {result}")

        if result.get('status') == 'success':
            return Response({
                'status': 'success',
                'message': 'Reminder sent successfully',
                'communication_id': result.get('communication_id'),
            })

        error_msg = result.get('message', 'Failed to send reminder')
        logger.error(f"Email sending failed: {error_msg}")
        return Response({'status': 'error', 'message': error_msg},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Personnel.DoesNotExist:
        logger.error(f"Personnel not found: {pk}")
        return Response({'status': 'error', 'message': 'Personnel not found'},
                        status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return Response({'status': 'error', 'message': f'Server error: {str(e)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_to_finance(request, pk):
    """Send complete documentation to finance (single, hardened implementation)."""
    try:
        personnel = Personnel.objects.get(id=pk)
    except Personnel.DoesNotExist:
        return Response({'error': 'Personnel not found'}, status=status.HTTP_404_NOT_FOUND)

    if not personnel.has_all_documents(context='routine'):
        return Response(
            {'error': 'Cannot send to finance. Documents are incomplete.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        payment, _ = Payment.objects.get_or_create(
            personnel=personnel,
            defaults={'meeting': personnel.meeting, 'purpose': 'dsa'},
        )
        payment.payment_status = 'submitted_to_finance'
        payment.finance_submission_date = timezone.now()
        payment.save()
    except Exception as e:
        logger.exception("send_to_finance: payment save failed")
        return Response({'error': f'Could not update payment: {e}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    email_warning = None
    try:
        email_service = EmailService()
        result = email_service.send_finance_submission_notification(personnel)
        if result.get('status') != 'success':
            email_warning = result.get('message', 'Unknown email error')
            logger.warning(
                f"send_to_finance: email to {personnel.email} failed: {email_warning}"
            )
    except Exception as e:
        email_warning = str(e)
        logger.warning(f"send_to_finance: email notification raised: {e}", exc_info=True)

    response_data = {
        'status': 'success',
        'message': 'Documents sent to finance successfully',
        'payment_id': payment.id,
    }
    if email_warning:
        response_data['warning'] = (
            f'Payment recorded, but email notification failed: {email_warning}'
        )

    return Response(response_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def calculate_payment(request, pk):
    """Calculate payment for personnel."""
    try:
        personnel = Personnel.objects.get(id=pk)
        calculator = PaymentCalculator(personnel)
        payment = calculator.calculate_payment()
        return Response(PaymentSerializer(payment).data)
    except Personnel.DoesNotExist:
        return Response({'error': 'Personnel not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def download_document(request, pk):
    """Download document file."""
    try:
        document = Document.objects.get(id=pk)
        return FileResponse(
            document.file.open('rb'),
            as_attachment=True,
            filename=document.file_name,
        )
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def generate_payment_report(request):
    """Generate payment report (Excel)."""
    payments = Payment.objects.all()
    report_data = []
    for payment in payments:
        report_data.append({
            'Name': payment.personnel.full_name(),
            'Role': payment.get_role_type_display() if hasattr(payment, 'get_role_type_display') else payment.role_type,
            'Purpose': payment.get_purpose_display() if hasattr(payment, 'get_purpose_display') else payment.purpose,
            'Nationality': payment.personnel.nationality,
            'Total Base': float(payment.total_base),
            'Travel Allowance': float(payment.travel_allowance),
            'Accommodation': float(payment.accommodation_allowance),
            'Per Diem': float(payment.per_diem),
            'Tax': float(payment.tax),
            'Total': float(payment.total_amount),
            'Currency': payment.currency,
            'Status': payment.payment_status,
        })

    df = pd.DataFrame(report_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Payment Report', index=False)
    output.seek(0)
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename=payment_report.xlsx'
    return response


# ============================================================
# WEB VIEWS
# ============================================================

def dashboard(request):
    """Main dashboard view."""
    context = {
        'total_personnel': Personnel.objects.count(),
        'total_interpreters': Personnel.objects.filter(profession='interpreter').count(),
        'total_translators': Personnel.objects.filter(profession='translator').count(),
        'complete_profiles': Personnel.objects.filter(documents_complete=True).count(),
        'incomplete_profiles': Personnel.objects.filter(documents_complete=False).count(),
        'pending_payments': Payment.objects.filter(payment_status='pending').count(),
        'submitted_payments': Payment.objects.filter(payment_status='submitted_to_finance').count(),
        'recent_personnel': Personnel.objects.order_by('-created_at')[:5],
        'recent_documents': Document.objects.order_by('-upload_date')[:5],
        'recent_communications': CommunicationLog.objects.order_by('-sent_date')[:5],
    }
    return render(request, 'personnel/dashboard.html', context)


def personnel_list(request):
    """List all personnel grouped by meeting and category."""
    personnel_qs = (
        Personnel.objects.all()
        .select_related('meeting')
        .order_by('last_name', 'first_name')
    )

    q = request.GET.get('q', '').strip()
    designation_filter = request.GET.get('designation', '').strip()
    doc_status_filter = request.GET.get('doc_status', '').strip()

    # Search across personnel + meeting
    if q:
        for word in q.split():
            personnel_qs = personnel_qs.filter(
                Q(first_name__icontains=word) |
                Q(last_name__icontains=word) |
                Q(email__icontains=word) |
                Q(nationality__icontains=word) |
                Q(designation__icontains=word) |
                Q(meeting__name__icontains=word) |
                Q(meeting__location__icontains=word)
            )

    # Designation filter
    if designation_filter == 'translator':
        personnel_qs = personnel_qs.filter(profession='translator')
    elif designation_filter == 'interpreter':
        personnel_qs = personnel_qs.filter(profession='interpreter')
    elif designation_filter == 'coordination':
        personnel_qs = personnel_qs.exclude(profession__in=['translator', 'interpreter'])

    # Doc status
    if doc_status_filter == 'complete':
        personnel_qs = personnel_qs.filter(documents_complete=True)
    elif doc_status_filter == 'incomplete':
        personnel_qs = personnel_qs.filter(documents_complete=False)
    elif doc_status_filter == 'pending_payment':
        personnel_qs = personnel_qs.filter(
            Q(payments__isnull=True) | Q(payments__payment_status='pending')
        ).distinct()

    # Grouping — same as before
    meetings_dict = {}
    personnel_without_meeting = []
    for person in personnel_qs:
        if person.meeting:
            key = person.meeting.id
            if key not in meetings_dict:
                meetings_dict[key] = {
                    'meeting': person.meeting,
                    'translators': [], 'interpreters': [], 'coordination': [],
                }
            if person.profession == 'translator':
                meetings_dict[key]['translators'].append(person)
            elif person.profession == 'interpreter':
                meetings_dict[key]['interpreters'].append(person)
            else:
                meetings_dict[key]['coordination'].append(person)
        else:
            personnel_without_meeting.append(person)

    grouped_meetings = []
    for data in meetings_dict.values():
        data['total'] = len(data['translators']) + len(data['interpreters']) + len(data['coordination'])
        grouped_meetings.append(data)
    grouped_meetings.sort(key=lambda x: x['meeting'].name)

    paginator = Paginator(grouped_meetings, 5)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'grouped_meetings': page_obj,
        'personnel_without_meeting': personnel_without_meeting,
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
        'total_count': personnel_qs.count(),
        'meetings': Meeting.objects.all().order_by('name'),
        'filters': {
            'q': q,
            'designation': designation_filter,
            'doc_status': doc_status_filter,
        },
    }
    return render(request, 'personnel/personnel_list.html', context)


def personnel_detail(request, pk):
    """View personnel details with dynamic document requirements."""
    personnel = get_object_or_404(Personnel, id=pk)
    documents = personnel.documents.all()
    payments = personnel.payments.all()

    document_dict = {doc.document_type: doc for doc in documents}

    required_docs = personnel.get_required_documents(context='routine')
    missing_docs = personnel.get_missing_documents(context='routine')
    # Bonus: expose travel-required docs too so the template can show them
    required_docs_travel = personnel.get_required_documents(context='travel')
    missing_docs_travel = personnel.get_missing_documents(context='travel')

    context = {
        'personnel': personnel,
        'documents': documents,
        'payments': payments,
        'document_dict': document_dict,
        'required_docs': required_docs,
        'missing_documents': missing_docs,
        'required_docs_travel': required_docs_travel,
        'missing_documents_travel': missing_docs_travel,
        'document_status': personnel.get_document_status(context='routine'),
        'document_status_travel': personnel.get_document_status(context='travel'),
        'document_types': Document.DOCUMENT_TYPES,
    }
    return render(request, 'personnel/personnel_detail.html', context)


def upload_document(request, personnel_id):
    """Upload document for personnel."""
    personnel = get_object_or_404(Personnel, id=personnel_id)

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES, personnel=personnel)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.personnel = personnel
            doc.save()

            if personnel.has_all_documents(context='routine'):
                personnel.documents_complete = True
                personnel.save(update_fields=['documents_complete'])

            messages.success(request, f'{doc.get_document_type_display()} uploaded successfully.')
            return redirect('personnel-detail', pk=personnel.id)
    else:
        form = DocumentUploadForm(personnel=personnel)

    return render(request, 'personnel/upload_modal.html', {
        'form': form,
        'personnel': personnel,
        'required_docs': personnel.get_required_documents(context='routine'),
    })


def upload_document_view(request, pk):
    """Upload document view for personnel."""
    personnel = get_object_or_404(Personnel, id=pk)

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.personnel = personnel
            doc.save()
            messages.success(request, f'Document uploaded successfully for {personnel.full_name()}')
            return redirect('personnel-detail', pk=personnel.id)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = DocumentUploadForm()

    return render(request, 'personnel/document_upload.html', {
        'form': form,
        'personnel': personnel,
    })


def payment_detail(request, pk):
    """View payment details."""
    payment = get_object_or_404(Payment, id=pk)
    return render(request, 'personnel/payment_detail.html', {'payment': payment})


from .forms import AFRICAN_COUNTRIES, AFRICAN_CAPITALS


def personnel_create(request, meeting_id=None):
    """Create a new personnel (with master-list dropdown)."""
    if request.method == 'POST':
        form = PersonnelForm(request.POST, request.FILES)
        if form.is_valid():
            personnel = form.save()
            messages.success(request, f'Personnel "{personnel.full_name()}" added successfully!')
            return redirect('personnel-list')
        for field, errors in form.errors.items():
            for error in errors:
                label = form.fields[field].label if field in form.fields else field
                messages.error(request, f'{label}: {error}')
    else:
        initial = {}
        if meeting_id:
            try:
                meeting = Meeting.objects.get(id=meeting_id)
                initial['meeting'] = meeting
            except Meeting.DoesNotExist:
                messages.warning(request, 'The specified meeting does not exist.')
        form = PersonnelForm(initial=initial)

    # Build the master lookup for the JS
    master_records = PersonnelMaster.objects.filter(is_active=True)
    master_lookup = {
        str(m.id): {
            'first_name':        m.first_name,
            'middle_name':       m.middle_name,
            'last_name':         m.last_name,
            'gender':            m.gender,
            'nationality':       m.nationality,
            'email':             m.email,
            'phone':             m.phone,
            'alternative_phone': m.alternate_phone,
            'date_of_birth':     m.date_of_birth.isoformat() if m.date_of_birth else '',
            'city_departure':    m.city_departure,
        }
        for m in master_records
    }

    context = {
        'form': form,
        'picker': PersonnelMasterPickerForm(),
        'master_lookup_json': json.dumps(master_lookup),
        'is_edit': False,

        # ↓↓↓ dropdown lists for the modal ↓↓↓
        'african_countries': AFRICAN_COUNTRIES,
        #'african_country_capitals': AFRICAN_COUNTRY_CAPITALS,
        #'african_country_capitals': AFRICAN_COUNTRY_CAPITALS,
        'african_capitals': AFRICAN_CAPITALS,  
    }
    return render(request, 'personnel/personnel_form.html', context)

# def personnel_create(request, meeting_id=None):
#     """Create a new personnel."""
#     if request.method == 'POST':
#         form = PersonnelForm(request.POST, request.FILES)
#         if form.is_valid():
#             personnel = form.save()
#             messages.success(request, f'Personnel "{personnel.full_name()}" added successfully!')
#             return redirect('personnel-list')
#         for field, errors in form.errors.items():
#             for error in errors:
#                 label = form.fields[field].label if field in form.fields else field
#                 messages.error(request, f'{label}: {error}')
#     else:
#         initial = {}
#         if meeting_id:
#             try:
#                 meeting = Meeting.objects.get(id=meeting_id)
#                 initial['meeting'] = meeting
#             except Meeting.DoesNotExist:
#                 messages.warning(request, 'The specified meeting does not exist.')
#         form = PersonnelForm(initial=initial)

#     return render(request, 'personnel/personnel_form.html', {
#         'form': form,
#         'is_edit': False,
#     })


@csrf_exempt
@staff_member_required
def create_meeting_ajax(request):
    """AJAX endpoint to create a meeting."""
    if request.method == 'POST':
        data = json.loads(request.body)
        name = data.get('name')
        location = data.get('location')
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if not all([name, location, start_date, end_date]):
            return JsonResponse({'error': 'All fields are required.'}, status=400)

        meeting = Meeting.objects.create(
            name=name,
            location=location,
            start_date=start_date,
            end_date=end_date,
            status='upcoming',
        )
        return JsonResponse({
            'id': meeting.id,
            'name': meeting.name,
            'location': meeting.location,
            'start_date': meeting.start_date.isoformat(),
            'end_date': meeting.end_date.isoformat(),
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)


def meeting_create(request):
    """View to create a new meeting."""
    if request.method == 'POST':
        form = MeetingForm(request.POST)
        if form.is_valid():
            meeting = form.save()
            messages.success(request, f'Meeting "{meeting.name}" created successfully!')
            return redirect('personnel-add-with-meeting', meeting_id=meeting.id)
    else:
        form = MeetingForm()
    return render(request, 'personnel/meeting_form.html', {'form': form})


def replace_document(request, doc_id):
    """Replace an existing document."""
    document = get_object_or_404(Document, id=doc_id)
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            if document.file:
                default_storage.delete(document.file.path)
            form.save()
            messages.success(request, f'{document.get_document_type_display()} replaced successfully.')
            return redirect('personnel-detail', pk=document.personnel.id)
    else:
        form = DocumentUploadForm(instance=document)
    return render(request, 'personnel/upload_modal.html', {
        'form': form,
        'document': document,
        'personnel': document.personnel,
    })


def download_document_view(request, doc_id):
    """Download a document (web view)."""
    document = get_object_or_404(Document, id=doc_id)
    return FileResponse(
        document.file.open('rb'),
        as_attachment=True,
        filename=document.file.name,
    )


def view_document(request, doc_id):
    """View a document inline."""
    document = get_object_or_404(Document, id=doc_id)
    return FileResponse(document.file.open('rb'), content_type=document.mime_type)


# ============================================================
# DOCUMENT MERGING
# ============================================================

def merge_documents_view(request, pk):
    """View to merge all documents for a personnel."""
    personnel = get_object_or_404(Personnel, id=pk)
    merger = DocumentMerger(personnel)

    summary = merger.get_merge_summary()
    documents = personnel.documents.all()
    document_dict = {doc.document_type: doc for doc in documents}

    context = {
        'personnel': personnel,
        'merger': merger,
        'document_status': merger.get_document_status(),
        'has_all_documents': merger.has_all_documents(),
        'missing_docs': merger.get_missing_documents_display(),
        'required_docs': merger.required_docs,
        'required_docs_display': [
            merger.DOC_DISPLAY_NAMES.get(doc, doc.title().replace('_', ' '))
            for doc in merger.required_docs
        ],
        'summary': summary,
        'documents': document_dict,
    }
    return render(request, 'personnel/merge_documents.html', context)


def merge_documents_download(request, pk, format='pdf'):
    """Merge all documents for a personnel and download the result."""
    personnel = get_object_or_404(Personnel, id=pk)
    merger = DocumentMerger(personnel)

    if not merger.has_all_documents():
        missing = merger.get_missing_documents_display()
        messages.error(request, f'Cannot merge: Missing documents - {", ".join(missing)}')
        return redirect('personnel-detail', pk=personnel.id)

    merge_record = DocumentMerge.objects.create(
        personnel=personnel,
        format=format,
        status='pending',
        missing_documents=merger.missing_docs,
        total_documents=len(merger.required_docs),
        created_by=request.user if request.user.is_authenticated else None,
    )

    try:
        success, content, filename, error = merger.merge_and_download(format)

        if success:
            merge_record.status = 'completed'
            merge_record.completed_at = timezone.now()
            merge_record.file_size = len(content)
            merge_record.output_file.save(filename, ContentFile(content))
            merge_record.save()

            content_type = 'application/pdf' if format == 'pdf' else 'application/zip'
            response = HttpResponse(content, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        else:
            merge_record.status = 'failed'
            merge_record.error_message = error
            merge_record.save()
            messages.error(request, f'Error merging documents: {error}')
            return redirect('personnel-detail', pk=personnel.id)

    except Exception as e:
        merge_record.status = 'failed'
        merge_record.error_message = str(e)
        merge_record.save()
        messages.error(request, f'Error merging documents: {str(e)}')
        return redirect('personnel-detail', pk=personnel.id)


def merge_documents_api(request, pk):
    """API endpoint to merge documents and return the file."""
    try:
        personnel = Personnel.objects.get(id=pk)
        format_type = request.GET.get('format', 'pdf')
        merger = DocumentMerger(personnel)

        if not merger.has_all_documents():
            return JsonResponse({
                'success': False,
                'error': f'Missing documents: {", ".join(merger.get_missing_documents_display())}',
                'missing_documents': merger.get_missing_documents_display(),
                'document_status': merger.get_document_status(),
                'required_documents': merger.required_docs,
            }, status=400)

        success, content, filename, error = merger.merge_and_download(format_type)

        if success:
            content_type = 'application/pdf' if format_type == 'pdf' else 'application/zip'
            response = HttpResponse(content, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        return JsonResponse({'success': False, 'error': error}, status=500)

    except Personnel.DoesNotExist:
        return JsonResponse({'error': 'Personnel not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def merge_documents_status_api(request, pk):
    """API endpoint to check document merge status."""
    try:
        personnel = Personnel.objects.get(id=pk)
        merger = DocumentMerger(personnel)

        return JsonResponse({
            'success': True,
            'personnel_id': personnel.id,
            'personnel_name': personnel.full_name(),
            'profession': personnel.profession,
            'employment_basis': personnel.employment_basis,
            'payment_method': personnel.payment_method,
            'category_label': personnel.category_label,
            'has_all_documents': merger.has_all_documents(),
            'missing_documents': merger.get_missing_documents_display(),
            'document_status': merger.get_document_status(),
            'total_required': len(merger.required_docs),
            'total_uploaded': len([d for d in merger.required_docs if d in merger.documents]),
            'required_documents': merger.required_docs,
            'required_documents_display': [
                merger.DOC_DISPLAY_NAMES.get(doc, doc.title().replace('_', ' '))
                for doc in merger.required_docs
            ],
        })
    except Personnel.DoesNotExist:
        return JsonResponse({'error': 'Personnel not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def merge_history_view(request):
    """View to show document merge history."""
    merges = DocumentMerge.objects.select_related('personnel', 'created_by').all().order_by('-created_at')

    context = {
        'merges': merges,
        'total_merges': merges.count(),
        'completed': merges.filter(status='completed').count(),
        'failed': merges.filter(status='failed').count(),
        'pending': merges.filter(status='pending').count(),
    }
    return render(request, 'personnel/merge_history.html', context)


def check_merged_status(request, pk):
    """API endpoint to check if a merged PDF exists."""
    try:
        personnel = Personnel.objects.get(id=pk)
        latest = MergedDocument.get_latest_for_personnel(personnel)
        merger = DocumentMerger(personnel)
        filesystem_merged = merger.has_merged_pdf()

        return JsonResponse({
            'success': True,
            'has_merged_pdf': bool(latest) or filesystem_merged,
            'merged_pdf_url': latest.pdf_file.url if latest else None,
            'merged_at': latest.created_at.isoformat() if latest else None,
            'total_documents': latest.total_documents if latest else 0,
            'has_all_documents': merger.has_all_documents(),
            'missing_documents': merger.get_missing_documents_display(),
        })
    except Personnel.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Personnel not found'}, status=404)


# ============================================================
# PAYMENT DETAIL VIEW
# ============================================================

def payment_detail_view(request, pk):
    """View payment details."""
    payment = get_object_or_404(Payment, id=pk)
    context = {
        'payment': payment,
        'personnel': payment.personnel,
        'meeting': payment.meeting,
        'status_badge_class': {
            'pending': 'warning',
            'submitted_to_finance': 'info',
            'approved': 'primary',
            'paid': 'success',
            'rejected': 'danger',
        },
    }
    return render(request, 'personnel/payment_receipt.html', context)


# ============================================================
# PERSONNEL EDIT / DELETE
# ============================================================

def personnel_edit(request, pk):
    personnel = get_object_or_404(Personnel, id=pk)

    if request.method == 'POST':
        form = PersonnelForm(request.POST, request.FILES, instance=personnel)
        if form.is_valid():
            saved = form.save()
            messages.success(request, f'Personnel "{saved.full_name()}" updated successfully!')
            return redirect('personnel-detail', pk=personnel.id)
        for field, errors in form.errors.items():
            for error in errors:
                label = form.fields[field].label if field in form.fields else field
                messages.error(request, f'{label}: {error}')
    else:
        form = PersonnelForm(instance=personnel)

    context = {
        'form': form,
        'personnel': personnel,
        'is_edit': True,
        'african_countries': AFRICAN_COUNTRIES,
        #'african_country_capitals': AFRICAN_COUNTRY_CAPITALS,
        'african_capitals': AFRICAN_CAPITALS, 
    }
    return render(request, 'personnel/personnel_form.html', context)

def personnel_delete(request, pk):
    """Delete personnel."""
    personnel = get_object_or_404(Personnel, id=pk)

    if request.method == 'POST':
        name = personnel.full_name()
        personnel.delete()
        messages.success(request, f'Personnel "{name}" deleted successfully!')
        return redirect('personnel-list')

    return render(request, 'personnel/personnel_confirm_delete.html', {'personnel': personnel})


# ============================================================
# PAYMENT SETTINGS
# ============================================================

@staff_member_required
def payment_settings_view(request):
    """View to manage payment rates."""
    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('rate_'):
                rate_type = key.replace('rate_', '')
                try:
                    setting = PaymentSetting.objects.get(rate_type=rate_type)
                    setting.value = value
                    setting.updated_by = request.user
                    setting.save()
                except PaymentSetting.DoesNotExist:
                    PaymentSetting.objects.create(
                        rate_type=rate_type,
                        value=value,
                        updated_by=request.user,
                    )
        messages.success(request, 'Payment rates updated successfully!')
        return redirect('payment-settings')

    rates = {}
    for rate_type, label in PaymentSetting.RATE_TYPES:
        try:
            setting = PaymentSetting.objects.get(rate_type=rate_type)
            rates[rate_type] = {
                'label': label,
                'value': setting.value,
                'id': setting.id,
            }
        except PaymentSetting.DoesNotExist:
            rates[rate_type] = {
                'label': label,
                'value': Decimal('0.00'),
                'id': None,
            }

    return render(request, 'personnel/payment_settings.html', {
        'rates': rates,
        'title': 'Payment Rate Settings',
    })


# ============================================================
# DASHBOARD TABLE (grouped by profession)
# ============================================================

def get_personnel_group(person):
    """Determine the group for a personnel (uses new profession field)."""
    if person.profession == 'translator':
        return 'Translators'
    if person.profession == 'interpreter':
        return 'Interpreters'
    return 'Coordination Team'


def personnel_dashboard(request):
    """Display meetings + their personnel with meeting-title search and pagination."""

    q = request.GET.get('q', '').strip()
    designation_filter = request.GET.get('designation', '').strip()
    doc_status_filter = request.GET.get('doc_status', '').strip()

    matching_meeting_ids = set()

    # ---- Meetings matching the search term ----
    if q:
        words = q.split()
        meeting_q = Q()
        for w in words:
            meeting_q &= (Q(name__icontains=w) | Q(location__icontains=w))
        matching_meeting_ids.update(
            Meeting.objects.filter(meeting_q).values_list('id', flat=True)
        )

    # ---- Personnel matching the search term ----
    personnel_qs = Personnel.objects.select_related('meeting').all()
    if q:
        words = q.split()
        p_q = Q()
        for w in words:
            p_q &= (
                Q(first_name__icontains=w) |
                Q(last_name__icontains=w) |
                Q(email__icontains=w) |
                Q(nationality__icontains=w) |
                Q(designation__icontains=w)
            )
        personnel_qs = personnel_qs.filter(p_q)
        matching_meeting_ids.update(
            personnel_qs.exclude(meeting__isnull=True)
                        .values_list('meeting_id', flat=True)
        )

    # ---- Designation / doc_status filters narrow the meeting set ----
    if designation_filter == 'translator':
        personnel_qs = personnel_qs.filter(profession='translator')
    elif designation_filter == 'interpreter':
        personnel_qs = personnel_qs.filter(profession='interpreter')
    elif designation_filter == 'coordination':
        personnel_qs = personnel_qs.exclude(
            profession__in=['translator', 'interpreter']
        )

    if designation_filter:
        matching_meeting_ids = set(
            personnel_qs.exclude(meeting__isnull=True)
                        .values_list('meeting_id', flat=True)
        )

    # ---- Which meetings to display ----
    if q or designation_filter or doc_status_filter:
        meetings_to_show = Meeting.objects.filter(
            id__in=matching_meeting_ids
        ).order_by('name')
    else:
        meetings_to_show = Meeting.objects.all().order_by('name')

    # ---- Paginate meetings ----
    paginator = Paginator(meetings_to_show, 5)   # change to 1 for testing
    page_obj = paginator.get_page(request.GET.get('page'))

    # ---- Build grouped_meetings for this page ----
    grouped_meetings = []
    for meeting in page_obj:
        people = list(Personnel.objects.filter(meeting=meeting))

        if designation_filter == 'translator':
            people = [p for p in people if p.profession == 'translator']
        elif designation_filter == 'interpreter':
            people = [p for p in people if p.profession == 'interpreter']
        elif designation_filter == 'coordination':
            people = [p for p in people if p.profession not in ('translator', 'interpreter')]

        if doc_status_filter == 'complete':
            people = [p for p in people if p.has_all_documents()]
        elif doc_status_filter == 'incomplete':
            people = [p for p in people if not p.has_all_documents()]
        elif doc_status_filter == 'pending_payment':
            people = [
                p for p in people
                if not p.payments.exists()
                or p.payments.first().payment_status == 'pending'
            ]

        grouped_meetings.append({
            'meeting': meeting,
            'translators':  [p for p in people if p.profession == 'translator'],
            'interpreters': [p for p in people if p.profession == 'interpreter'],
            'coordination': [p for p in people if p.profession not in ('translator', 'interpreter')],
            'total': len(people),
        })

    # ---- Orphans ----
    personnel_without_meeting = Personnel.objects.filter(meeting__isnull=True)
    if q:
        p_q = Q()
        for w in q.split():
            p_q &= (
                Q(first_name__icontains=w) |
                Q(last_name__icontains=w) |
                Q(email__icontains=w)
            )
        personnel_without_meeting = personnel_without_meeting.filter(p_q)

    context = {
        'grouped_meetings': grouped_meetings,
        'personnel_without_meeting': personnel_without_meeting,
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
        'total_count': Personnel.objects.count(),
        'complete_count': Personnel.objects.filter(documents_complete=True).count(),
        'incomplete_count': Personnel.objects.filter(documents_complete=False).count(),
        'pending_payments': Payment.objects.filter(payment_status='pending').count(),
        'filters': {
            'q': q,
            'designation': designation_filter,
            'doc_status': doc_status_filter,
        },
    }
    return render(request, 'personnel/dashboard_table.html', context)


def debug_view(request):
    """Debug view to check data."""
    data = []
    for p in Personnel.objects.select_related('meeting').all():
        data.append({
            'name': p.full_name(),
            'profession': p.profession,
            'employment_basis': p.employment_basis,
            'payment_method': p.payment_method,
            'meeting': p.meeting.name if p.meeting else None,
        })
    return JsonResponse({'personnel': data, 'total': len(data)})


# ============================================================
# AUTHENTICATED SELF-SERVICE VIEWS
# ============================================================

def login_view(request):
    """Custom login page."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        messages.error(request, 'Invalid username or password.')

    return render(request, 'registration/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def home_view(request):
    """Role-based home redirect."""
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.is_superuser or request.user.is_staff:
        return redirect('dashboard')

    assignment = getattr(request.user, 'meeting_assignment', None)
    if not assignment or not assignment.is_active:
        return render(request, 'personnel/no_assignment.html')

    if assignment.role == 'interpreter':
        return redirect('interpreter-dashboard')
    if assignment.role == 'translator':
        return redirect('translator-dashboard')
    if assignment.role == 'coordinator':
        return redirect('coordinator-dashboard')
    return redirect('login')


def _require_assignment(request, allowed_roles=None):
    """Helper: return the user's assignment or raise 403."""
    if not request.user.is_authenticated:
        return None, redirect('login')
    if request.user.is_superuser or request.user.is_staff:
        return None, HttpResponseForbidden("Admins use the admin dashboard.")
    assignment = getattr(request.user, 'meeting_assignment', None)
    if not assignment or not assignment.is_active:
        return None, HttpResponseForbidden("No active assignment.")
    if allowed_roles and assignment.role not in allowed_roles:
        return None, HttpResponseForbidden("Not allowed for your role.")
    return assignment, None


def _build_dashboard_context(assignment, context_name='routine'):
    """Common context for all three role dashboards."""
    personnel = assignment.personnel
    meeting = assignment.meeting

    documents = {d.document_type: d for d in personnel.documents.all()}
    required = personnel.get_required_documents(context=context_name)
    display_names = personnel.get_document_type_display_names(context=context_name)

    rows = []
    for idx, doc_type in enumerate(required, 1):
        doc = documents.get(doc_type)
        rows.append({
            'order': idx,
            'doc_type': doc_type,
            'display_name': display_names.get(doc_type, doc_type.replace('_', ' ').title()),
            'document': doc,
            'uploaded': doc is not None,
            'verified': doc.is_verified if doc else False,
            'upload_date': doc.upload_date if doc else None,
        })

    missing = [r['display_name'] for r in rows if not r['uploaded']]

    return {
        'assignment': assignment,
        'personnel': personnel,
        'meeting': meeting,
        'rows': rows,
        'missing': missing,
        'has_all': len(missing) == 0,
        'total_required': len(rows),
        'total_uploaded': sum(1 for r in rows if r['uploaded']),
        'category_label': personnel.category_label,
    }


@login_required
def interpreter_dashboard(request):
    assignment, err = _require_assignment(request, allowed_roles=['interpreter'])
    if err:
        return err
    return render(request, 'personnel/interpreter_dashboard.html',
                  _build_dashboard_context(assignment))


@login_required
def translator_dashboard(request):
    assignment, err = _require_assignment(request, allowed_roles=['translator'])
    if err:
        return err
    return render(request, 'personnel/translator_dashboard.html',
                  _build_dashboard_context(assignment))


@login_required
def coordinator_dashboard(request):
    assignment, err = _require_assignment(request, allowed_roles=['coordinator'])
    if err:
        return err
    return render(request, 'personnel/coordinator_dashboard.html',
                  _build_dashboard_context(assignment))


@login_required
def my_meeting_upload(request, doc_type):
    """Upload a document for the currently logged-in personnel."""
    if request.user.is_superuser or request.user.is_staff:
        return HttpResponseForbidden("Admins use the admin dashboard.")

    assignment = getattr(request.user, 'meeting_assignment', None)
    if not assignment or not assignment.is_active:
        return HttpResponseForbidden("No active assignment.")

    personnel = assignment.personnel
    required = personnel.get_required_documents(context='routine')

    if doc_type not in required:
        messages.error(request, f"'{doc_type}' is not required for your role.")
        return redirect('home')

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES, personnel=personnel)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.personnel = personnel
            doc.document_type = doc_type
            doc.save()

            service = AccountService()
            service.send_upload_notification_to_admin(personnel, doc)

            if personnel.has_all_documents(context='routine'):
                personnel.documents_complete = True
                personnel.save(update_fields=['documents_complete'])
                service = AccountService()
                service.send_documents_complete_notification(personnel)
            messages.success(request, f"{doc.get_document_type_display()} uploaded successfully.")
            return redirect('home')
        messages.error(request, "Please correct the errors below.")
    else:
        form = DocumentUploadForm(personnel=personnel, initial={'document_type': doc_type})

    form.fields['document_type'].choices = [(doc_type, doc_type.replace('_', ' ').title())]
    form.fields['document_type'].widget = forms.HiddenInput()

    return render(request, 'personnel/my_meeting_upload.html', {
        'form': form,
        'doc_type': doc_type,
        'personnel': personnel,
        'assignment': assignment,
    })


# ============================================================
# ADMIN: DEMAND AVAILABILITY
# ============================================================

@staff_member_required
def demand_availability(request, pk):
    """Admin action: create user + assignment + email credentials."""
    if request.method != 'POST':
        return HttpResponseForbidden(
            "Method not allowed. Use the button on the personnel detail page."
        )

    personnel = get_object_or_404(Personnel, id=pk)

    if not personnel.meeting:
        messages.error(request, "Assign this person to a meeting first.")
        return redirect('personnel-detail', pk=personnel.id)

    service = AccountService()
    admin_email = request.user.email or None

    existing = MeetingAssignment.objects.filter(
        personnel=personnel, meeting=personnel.meeting
    ).first()

    if existing:
        new_password = MeetingAssignment.generate_password()
        existing.user.set_password(new_password)
        existing.user.save()
        existing.plain_password_hint = new_password
        existing.save(update_fields=['plain_password_hint'])

        ok, err = service.send_credentials_email(existing, admin_email=admin_email)
        if ok:
            messages.success(
                request,
                f"Credentials re-sent to {personnel.email} "
                f"(username: {existing.username_for_meeting})."
            )
        else:
            messages.warning(
                request,
                f"Email failed: {err}. New password: {new_password} — "
                f"please share manually."
            )
        return redirect('personnel-detail', pk=personnel.id)

    try:
        assignment, plain_password = service.create_account_for_personnel(personnel)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('personnel-detail', pk=personnel.id)

    ok, err = service.send_credentials_email(assignment, admin_email=admin_email)

    if ok:
        messages.success(
            request,
            f"Account created for {personnel.full_name()} "
            f"(username: {assignment.username_for_meeting}). "
            f"Credentials emailed to {personnel.email}."
        )
    else:
        messages.warning(
            request,
            f"Account created for {personnel.full_name()} "
            f"(username: {assignment.username_for_meeting}), "
            f"but email failed: {err}. "
            f"Temporary password: {plain_password} — please share manually and delete this message."
        )

    return redirect('personnel-detail', pk=personnel.id)


# ============================================================
# AVAILABILITY WORKFLOW
# ============================================================

@staff_member_required
@require_POST
def request_availability(request, pk):
    """Admin: send availability invitation to one personnel."""
    personnel = get_object_or_404(Personnel, id=pk)

    if not personnel.meeting:
        messages.error(request, "Assign this person to a meeting first.")
        return redirect('personnel-detail', pk=personnel.id)

    ar, _ = AvailabilityRequest.objects.get_or_create(
        personnel=personnel,
        meeting=personnel.meeting,
    )

    if ar.status == 'declined':
        messages.warning(request, "This person already declined. Cannot re-invite.")
        return redirect('personnel-detail', pk=personnel.id)

    if ar.status in ('available', 'approved'):
        messages.info(request, "This person already responded or is approved.")
        return redirect('personnel-detail', pk=personnel.id)

    service = AccountService()
    ok, err = service.send_availability_invitation(ar, request=request)
    if ok:
        messages.success(request, f"Availability request sent to {personnel.email}.")
    else:
        messages.error(request, f"Failed to send: {err}")

    return redirect('personnel-detail', pk=personnel.id)


def availability_respond(request, token):
    """Public endpoint. Person clicks Yes or No in the email."""
    try:
        req_id, response = parse_response_token(token)
    except SignatureExpired:
        return render(request, 'personnel/availability_expired.html')
    except BadSignature:
        return render(request, 'personnel/availability_invalid.html')

    if response not in ('yes', 'no'):
        return render(request, 'personnel/availability_invalid.html')

    ar = get_object_or_404(AvailabilityRequest, id=req_id)

    if ar.status not in ('pending', 'expired'):
        return render(request, 'personnel/availability_already_responded.html', {
            'availability_request': ar,
        })

    service = AccountService()

    if response == 'yes':
        ar.status = 'available'
        ar.responded_at = timezone.now()
        ar.save(update_fields=['status', 'responded_at'])
        service.send_availability_response_to_admin(ar)
        return render(request, 'personnel/availability_thank_you.html', {
            'availability_request': ar, 'response': 'yes',
        })

    ar.status = 'declined'
    ar.responded_at = timezone.now()
    ar.save(update_fields=['status', 'responded_at'])
    service.send_availability_response_to_admin(ar)
    service.send_decline_acknowledgement(ar)
    return render(request, 'personnel/availability_thank_you.html', {
        'availability_request': ar, 'response': 'no',
    })


@staff_member_required
@require_POST
def approve_availability(request, pk):
    """Admin approves an 'available' person."""
    ar = get_object_or_404(AvailabilityRequest, id=pk)

    if ar.status != 'available':
        messages.error(request, "Only 'available' requests can be approved.")
        return redirect('personnel-detail', pk=ar.personnel.id)

    personnel = ar.personnel
    service = AccountService()

    try:
        assignment, plain_password = service.create_account_for_personnel(personnel)
    except ValueError as e:
        existing = MeetingAssignment.objects.filter(
            personnel=personnel, meeting=ar.meeting
        ).first()
        if not existing:
            messages.error(request, str(e))
            return redirect('personnel-detail', pk=personnel.id)
        assignment = existing
        plain_password = "(unchanged)"

    ok, err = service.send_credentials_email(assignment, admin_email=request.user.email or None)

    ar.status = 'approved'
    ar.approved_by = request.user
    ar.approved_at = timezone.now()
    ar.assignment = assignment
    ar.save(update_fields=['status', 'approved_by', 'approved_at', 'assignment'])

    service.send_approval_confirmation(ar)

    if ok:
        messages.success(
            request,
            f"Approved. Credentials sent to {personnel.email} "
            f"(username: {assignment.username_for_meeting})."
        )
    else:
        messages.warning(
            request,
            f"Approved, but credentials email failed: {err}. "
            f"Temporary password: {plain_password}"
        )

    return redirect('personnel-detail', pk=personnel.id)


@staff_member_required
@require_POST
def decline_availability(request, pk):
    """Admin marks someone as declined/not selected."""
    ar = get_object_or_404(AvailabilityRequest, id=pk)
    ar.status = 'declined'
    ar.save(update_fields=['status'])
    messages.info(request, "Marked as declined.")
    return redirect('personnel-detail', pk=ar.personnel.id)


@staff_member_required
def meeting_availability_dashboard(request, meeting_id):
    """List all availability requests for a meeting."""
    meeting = get_object_or_404(Meeting, id=meeting_id)
    requests = AvailabilityRequest.objects.filter(meeting=meeting).select_related(
        'personnel', 'assignment'
    ).order_by('status', 'personnel__last_name')

    context = {
        'meeting': meeting,
        'requests': requests,
        'pending': requests.filter(status='pending'),
        'available': requests.filter(status='available'),
        'approved': requests.filter(status='approved'),
        'declined': requests.filter(status='declined'),
    }
    return render(request, 'personnel/meeting_availability_dashboard.html', context)


@staff_member_required
@require_POST
def request_availability_bulk(request, meeting_id):
    """Send availability invitations to all personnel in a meeting who are still pending."""
    meeting = get_object_or_404(Meeting, id=meeting_id)
    personnel_qs = meeting.personnel.all()

    service = AccountService()
    sent = 0
    skipped = 0
    errors = []

    for p in personnel_qs:
        ar, _ = AvailabilityRequest.objects.get_or_create(
            personnel=p,
            meeting=meeting,
        )
        if ar.status in ('available', 'approved', 'declined'):
            skipped += 1
            continue

        ok, err = service.send_availability_invitation(ar, request=request)
        if ok:
            sent += 1
        else:
            errors.append(f"{p.full_name()}: {err}")

    if sent:
        messages.success(request, f"Sent {sent} invitation(s).")
    if skipped:
        messages.info(request, f"Skipped {skipped} already-responded.")
    if errors:
        messages.warning(request, f"Errors: {'; '.join(errors)}")

    return redirect('meeting-availability-dashboard', meeting_id=meeting.id)


# ============================================================
# PASSWORD CHANGE
# ============================================================

@login_required
def change_password_view(request):
    """First-login password change."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            profile.must_change_password = False
            profile.password_changed_at = timezone.now()
            profile.save()
            messages.success(request, "Your password has been updated.")
            return redirect('home')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'registration/change_password.html', {'form': form})


# ============================================================
# CONTACT FORM
# ============================================================

def contact_view(request):
    """Public contact form."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.ip_address = _client_ip(request)
            msg.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            msg.save()

            _send_contact_notification(msg)

            messages.success(
                request,
                "Thank you — your message has been sent. "
                "We'll get back to you within 2 business days."
            )
            return redirect('contact')
    else:
        form = ContactForm()

    return render(request, 'personnel/contact.html', {'form': form})


def _client_ip(request):
    """Best-effort client IP."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _send_contact_notification(contact_message):
    """Email the admin when a new contact message arrives."""
    admin_email = settings.DEFAULT_FROM_EMAIL
    if getattr(settings, 'ADMINS', None):
        admin_email = settings.ADMINS[0][1]

    subject = f"[Contact] {contact_message.subject} — {contact_message.name}"
    context = {'contact': contact_message}
    html = render_to_string('emails/contact_notification.html', context)
    text = strip_tags(html)

    try:
        mail = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[admin_email],
            reply_to=[contact_message.email],
        )
        mail.attach_alternative(html, "text/html")
        mail.send()
    except Exception as e:
        logger.error(f"Failed to send contact notification: {e}", exc_info=True)


# ============================================================
# PAYMENT CALCULATION REDIRECT
# ============================================================

def calculate_payment_and_redirect(request, person_id):
    """Calculate payment for a personnel and redirect to the payment detail."""
    person = get_object_or_404(Personnel, id=person_id)
    calculator = PaymentCalculator(person)
    payment = calculator.calculate_payment()
    messages.success(request, f"Payment calculated for {person.full_name()}.")
    return redirect('payment-detail', pk=payment.id)

# personnel/views.py — append these views

from .models import PersonnelExpense
from .forms import PersonnelExpenseForm


# ---------- Expense CRUD (web) ----------

@login_required
def expense_list(request):
    """List all expense records, filterable."""
    qs = PersonnelExpense.objects.select_related(
        'personnel', 'meeting', 'created_by'
    ).all()

    # Filters
    personnel_id = request.GET.get('personnel')
    if personnel_id:
        qs = qs.filter(personnel_id=personnel_id)

    category = request.GET.get('category')
    if category:
        qs = qs.filter(category=category)

    locked = request.GET.get('locked')
    if locked == 'yes':
        qs = qs.filter(is_locked=True)
    elif locked == 'no':
        qs = qs.filter(is_locked=False)

    search = request.GET.get('search')
    if search:
        qs = qs.filter(
            Q(personnel__first_name__icontains=search) |
            Q(personnel__last_name__icontains=search) |
            Q(country__icontains=search)
        )

    paginator = Paginator(qs, 20)
    page = request.GET.get('page', 1)
    try:
        expenses = paginator.page(page)
    except PageNotAnInteger:
        expenses = paginator.page(1)
    except EmptyPage:
        expenses = paginator.page(paginator.num_pages)

    # Totals by currency
    totals_by_currency = {}
    for exp in qs:
        cur = exp.currency
        totals_by_currency.setdefault(cur, Decimal('0.00'))
        totals_by_currency[cur] += exp.grand_total

    context = {
        'expenses': expenses,
        'page_obj': expenses,
        'is_paginated': expenses.has_other_pages(),
        'categories': PersonnelExpense.EXPENSE_CATEGORIES,
        'currencies': PersonnelExpense.CURRENCY_CHOICES,
        'totals_by_currency': totals_by_currency,
        'filters': {
            'personnel': personnel_id,
            'category': category,
            'locked': locked,
            'search': search,
        },
    }
    return render(request, 'personnel/expense_list.html', context)


@login_required
def expense_create(request):
    """Create a new manual expense record."""
    initial = {}

    # Pre-select personnel if coming from their detail page
    personnel_id = request.GET.get('personnel')
    if personnel_id:
        try:
            p = Personnel.objects.get(pk=personnel_id)
            initial['personnel'] = p
            initial['meeting'] = p.meeting
            # Guess category from profession / group
            if p.profession == 'translator':
                initial['category'] = 'translator_group_i'
            elif p.profession == 'interpreter':
                initial['category'] = 'interpreter_group_i'
            else:
                initial['category'] = 'coordinator'
        except Personnel.DoesNotExist:
            pass

    if request.method == 'POST':
        form = PersonnelExpenseForm(request.POST, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            expense.save()
            messages.success(
                request,
                f'Expense saved for {expense.personnel.full_name()} — '
                f'{expense.currency} {expense.grand_total:.2f}'
            )
            return redirect('expense-list')
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f'{field}: {error}')
    else:
        form = PersonnelExpenseForm(initial=initial, user=request.user)

    return render(request, 'personnel/expense_form.html', {
        'form': form,
        'is_edit': False,
    })


@login_required
def expense_edit(request, pk):
    """Edit an existing expense record (admins can edit locked records)."""
    expense = get_object_or_404(PersonnelExpense, id=pk)

    if request.method == 'POST':
        form = PersonnelExpenseForm(request.POST, instance=expense, user=request.user)
        if form.is_valid():
            saved = form.save()
            messages.success(
                request,
                f'Expense updated — {saved.currency} {saved.grand_total:.2f}'
            )
            return redirect('expense-list')
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f'{field}: {error}')
    else:
        form = PersonnelExpenseForm(instance=expense, user=request.user)

    return render(request, 'personnel/expense_form.html', {
        'form': form,
        'expense': expense,
        'is_edit': True,
    })


@login_required
def expense_detail(request, pk):
    """View a single expense record."""
    expense = get_object_or_404(
        PersonnelExpense.objects.select_related('personnel', 'meeting', 'created_by'),
        id=pk
    )
    return render(request, 'personnel/expense_detail.html', {'expense': expense})


@login_required
def expense_delete(request, pk):
    """Delete an expense (admins only for locked records)."""
    expense = get_object_or_404(PersonnelExpense, id=pk)

    if expense.is_locked and not request.user.is_staff:
        messages.error(request, "This record is locked. Only an admin can delete it.")
        return redirect('expense-detail', pk=expense.id)

    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense record deleted.')
        return redirect('expense-list')

    return render(request, 'personnel/expense_confirm_delete.html', {'expense': expense})


@login_required
def expense_toggle_lock(request, pk):
    """Admin: lock/unlock an expense record."""
    if not request.user.is_staff:
        return HttpResponseForbidden("Admins only.")

    expense = get_object_or_404(PersonnelExpense, id=pk)
    expense.is_locked = not expense.is_locked
    expense.save(update_fields=['is_locked'])
    messages.success(
        request,
        f'Record {"locked 🔒" if expense.is_locked else "unlocked 🔓"}.'
    )
    return redirect('expense-detail', pk=expense.id)


# ---------- Expense API (DRF) ----------

class PersonnelExpenseViewSet(viewsets.ModelViewSet):
    """REST API for expense records (used by admin frontend / integrations)."""
    queryset = PersonnelExpense.objects.select_related('personnel', 'meeting').all()
    serializer_class = PersonnelExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        personnel_id = self.request.query_params.get('personnel')
        if personnel_id:
            qs = qs.filter(personnel_id=personnel_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def toggle_lock(self, request, pk=None):
        expense = self.get_object()
        expense.is_locked = not expense.is_locked
        expense.save(update_fields=['is_locked'])
        return Response({
            'status': 'success',
            'is_locked': expense.is_locked,
            'grand_total': str(expense.grand_total),
        })
    
import json
from .models import PersonnelMaster
from .forms import PersonnelMasterPickerForm


def personnel_add_from_master(request):
    """
    Two-step Add-Personnel form:
      * First name is a dropdown from PersonnelMaster.
      * The rest of the fields are auto-filled from that record via JS.
      * The personnel form is saved as a normal Personnel.
    """
    # Build a lookup dict for the JS to use
    master_records = PersonnelMaster.objects.filter(is_active=True)
    master_lookup = {
        str(m.id): {
            'first_name':     m.first_name,
            'middle_name':    m.middle_name,
            'last_name':      m.last_name,
            'gender':         m.gender,
            'nationality':    m.nationality,
            'email':          m.email,
            'phone':          m.phone,
            'alternative_phone': m.alternate_phone,
            'date_of_birth':  m.date_of_birth.isoformat() if m.date_of_birth else '',
            'city_departure': m.city_departure,
        }
        for m in master_records
    }

    if request.method == 'POST':
        form = PersonnelForm(request.POST, request.FILES)
        if form.is_valid():
            personnel = form.save(commit=False)
            personnel.created_by = request.user if request.user.is_authenticated else None
            personnel.save()
            messages.success(
                request,
                f'Personnel "{personnel.full_name()}" added successfully!'
            )
            return redirect('personnel-list')
        for field, errors in form.errors.items():
            for error in errors:
                label = form.fields[field].label if field in form.fields else field
                messages.error(request, f'{label}: {error}')
    else:
        form = PersonnelForm()

    picker = PersonnelMasterPickerForm()

    context = {
        'form': form,
        'picker': picker,
        'master_lookup_json': json.dumps(master_lookup),
        'is_edit': False,
    }
    return render(request, 'personnel/personnel_add_from_master.html', context)

from .forms import PersonnelMasterForm

@csrf_exempt
@staff_member_required
def create_master_personnel_ajax(request):
    """AJAX endpoint: create a PersonnelMaster record and return its data."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Malformed JSON'}, status=400)

    form = PersonnelMasterForm(data=data)
    if not form.is_valid():
        # Return first error per field so the modal can display them inline
        return JsonResponse(
            {'error': 'Validation failed', 'errors': form.errors},
            status=400,
        )

    record = form.save()

    return JsonResponse({
        'id':              record.id,
        'label':           str(record),
        'first_name':      record.first_name,
        'middle_name':     record.middle_name,
        'last_name':       record.last_name,
        'gender':          record.gender or '',
        'nationality':     record.nationality or '',
        'email':           record.email or '',
        'phone':           record.phone or '',
        'alternate_phone': record.alternate_phone or '',
        'date_of_birth':   record.date_of_birth.isoformat() if record.date_of_birth else '',
        'city_departure':  record.city_departure or '',
    })