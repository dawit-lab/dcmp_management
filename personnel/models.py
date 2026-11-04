# personnel/models.py

import os
import secrets
import string
from decimal import Decimal

from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.core.exceptions import ValidationError


# ============================================================
# MEETING
# ============================================================

class Meeting(models.Model):
    """Meeting/Event details"""
    MEETING_STATUS = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=MEETING_STATUS, default='upcoming')
    description = models.TextField(blank=True)
    languages_required = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} - {self.location}"

    def days_duration(self):
        return (self.end_date - self.start_date).days + 1


# ============================================================
# FILE VALIDATORS
# ============================================================

def validate_photo_size(value):
    if value.size > 5 * 1024 * 1024:
        raise ValidationError("Photo file size cannot exceed 5MB.")


def validate_photo_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    if ext not in valid_extensions:
        raise ValidationError(f"Unsupported file extension. Allowed: {', '.join(valid_extensions)}")


def validate_file_size(value):
    filesize = value.size
    if filesize > 5242880:
        raise ValidationError("Maximum file size is 5MB")


# ============================================================
# PERSONNEL
# ============================================================

class Personnel(models.Model):
    """Base model for interpreters, translators, and coordination staff."""

    # ---- NEW: two-dimensional classification ----
    PROFESSION_CHOICES = [
        ('translator', 'Translator'),
        ('interpreter', 'Interpreter'),
        ('icoordination', 'Interpretation Coordination'),
        ('Tcoordination', 'Translation Coordination'),
        ('adminassistant', 'Administrative Assistant'),
        ('documentworkflowofficer', 'Document Workflow Officer'),
        ('conferencesystemtechnitians', 'Conference System Technicians'),
        ('documentationdistributionandcirculation', 'Documentation Distribution and Circulation'),
        ('documentationreproductionandprinting', 'Documentation Reproduction and Printing'),
        ('other', 'Other'),
    ]

    EMPLOYMENT_BASIS_CHOICES = [
        ('regular', 'Regular (permanent staff)'),
        ('contract', 'Contract (short-term from roster)'),
        ('freelance', 'Freelance / Online (per-assignment)'),
        ('daily', 'Daily (per-meeting)'),
        ('na', 'Not applicable'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('monthly_salary', 'Monthly Salary'),
        ('per_assignment', 'Per Assignment (word count, etc.)'),
        ('per_meeting', 'Per Meeting / Daily'),
        ('salary_plus_dsa', 'Monthly Salary + DSA on travel'),
    ]

    # ---- LEGACY (kept for backwards compatibility with views/templates) ----
    PERSONNEL_TYPES = [
        ('interpreter', 'Interpreter'),
        ('translator', 'Translator'),
        ('icoordination', 'Interpretation coordination'),
        ('Tcoordination', 'Translation coordination'),
        ('adminassistant', 'Administrative Assistant'),
        ('documentworkflowofficer', 'Document Workflow Officer'),
        ('conferencesystemtechnitians', 'Conference System Technicians'),
        ('documentationdistributionanandcirculation', 'Documentation Distribution and Circulation'),
        ('documentationreproductionandprinting', 'Documentation Reproduction and Printing'),
        ('both', 'Both'),
    ]

    TRANSLATOR_TYPES = [
        ('freelance', 'Freelance Translator'),
        ('staff', 'Staff Translator'),
    ]

    INTERPRETER_TYPES = [
        ('freelance', 'Freelance Interpreter'),
        ('staff', 'Staff Interpreter'),
    ]

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    nationality = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    alternative_phone = models.CharField(max_length=20, blank=True)

    # ---- NEW: canonical classification ----
    profession = models.CharField(
        max_length=50,
        choices=PROFESSION_CHOICES,
        default='interpreter',
        db_index=True,
    )
    employment_basis = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_BASIS_CHOICES,
        default='na',
        db_index=True,
    )
    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHOD_CHOICES,
        default='per_meeting',
        db_index=True,
    )

    # ---- LEGACY: kept for backwards compatibility ----
    personnel_type = models.CharField(
        max_length=50,
        choices=PERSONNEL_TYPES,
        default='interpreter',
        help_text="DEPRECATED — use profession + employment_basis instead.",
    )
    translator_type = models.CharField(
        max_length=20,
        choices=TRANSLATOR_TYPES,
        blank=True,
        null=True,
        help_text="DEPRECATED — maps to employment_basis.",
    )
    interpreter_type = models.CharField(
        max_length=20,
        choices=INTERPRETER_TYPES,
        blank=True,
        null=True,
        help_text="DEPRECATED — maps to employment_basis.",
    )

    # Professional assets
    photo = models.ImageField(
        upload_to='personnel_photos/%Y/%m/%d/',
        null=True,
        blank=True,
        validators=[validate_photo_extension, validate_photo_size],
        help_text="Upload a passport-style photo (JPG, PNG, GIF - max 5MB)",
    )
    designation = models.CharField(max_length=100, default='INTERPRETER')
    city_departure = models.CharField(max_length=200)
    languages = models.JSONField(default=list)

    # Assignment Details
    meeting = models.ForeignKey(Meeting, on_delete=models.SET_NULL, null=True, related_name='personnel')
    is_active = models.BooleanField(default=True)
    documents_complete = models.BooleanField(default=False)

        # ---- Travel / DSA eligibility ----
    travelled_abroad = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Travelled abroad for this meeting",
        help_text=(
            "True when this person travelled outside Addis Ababa / HQ "
            "to service the meeting. DSA and travel documents are only "
            "required when this is True."
        ),
    )
    travel_notes = models.TextField(
        blank=True,
        help_text="Optional notes on the travel (dates, itinerary, who approved).",
    )

    # Additional Information
    notes = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='created_personnel'
    )

    class Meta:
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['personnel_type']),
            models.Index(fields=['documents_complete']),
            models.Index(fields=['profession']),
            models.Index(fields=['employment_basis']),
            models.Index(fields=['payment_method']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_profession_display()}"

    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    # ------------------------------------------------------------
    # BACKWARD-COMPAT PROPERTIES
    # ------------------------------------------------------------
    @property
    def category_label(self):
        """Human label like 'Regular Translator', 'Daily Interpreter'."""
        prof = self.get_profession_display()
        basis = self.get_employment_basis_display() if self.employment_basis != 'na' else ''
        return f"{basis.split(' (')[0]} {prof}".strip()

    # ------------------------------------------------------------
    # DOCUMENT REQUIREMENTS
    # ------------------------------------------------------------
    def get_required_documents(self, context='routine'):
        """
        Return a list of required document types for the given context.

        context='routine' → documents needed for routine payment
        context='travel'  → documents needed for DSA when traveling abroad

        Deduplicates the result: a doc may match both a blank-basis row
        ("any basis") and a specific-basis row, in which case it should
        only appear once.
        """
        from django.db.models import Q as _Q

        # Travel context only applies if the person actually travelled.
        if context == 'travel' and not self.travelled_abroad:
            return []

        qs = DocumentRequirement.objects.filter(
            profession=self.profession,
            context=context,
            is_required=True,
        ).filter(
            _Q(employment_basis=self.employment_basis) | _Q(employment_basis='')
        )

        seen = set()
        result = []
        for doc in qs.values_list('document_type', flat=True):
            if doc not in seen:
                seen.add(doc)
                result.append(doc)
        return result

    def get_document_type_display_names(self, context='routine'):
        doc_map = Document.DISPLAY_NAMES
        required_docs = self.get_required_documents(context=context)
        return {doc: doc_map.get(doc, doc.title()) for doc in required_docs}

    def get_missing_documents(self, context='routine'):
        required_docs = self.get_required_documents(context=context)
        uploaded_docs = self.documents.filter(
            is_complete=True
        ).values_list('document_type', flat=True)
        return [doc for doc in required_docs if doc not in uploaded_docs]

    def has_all_documents(self, context='routine'):
        return len(self.get_missing_documents(context=context)) == 0

    def get_document_status(self, context='routine'):
        documents = self.documents.all()
        required_docs = self.get_required_documents(context=context)
        status = {}
        for doc_type in required_docs:
            doc = documents.filter(document_type=doc_type).first()
            status[doc_type] = {
                'uploaded': doc is not None,
                'verified': doc.is_verified if doc else False,
                'upload_date': doc.upload_date if doc else None,
                'file_name': doc.file_name if doc else None,
            }
        return status
    
    def get_all_missing_documents(self):
        """
        Union of routine + travel missing documents.
        Travel is only counted if the person travelled abroad.
        """
        missing = list(self.get_missing_documents('routine'))
        for doc in self.get_missing_documents('travel'):
            if doc not in missing:
                missing.append(doc)
        return missing

    def has_all_required_documents(self):
        """True only when both routine and (if applicable) travel are complete."""
        return len(self.get_all_missing_documents()) == 0
    
    def get_all_document_status(self):
        """
        Merged document status for routine + travel contexts.
        Travel keys are deduplicated against routine so each doc
        appears only once.
        """
        merged = dict(self.get_document_status('routine'))

        if self.travelled_abroad:
            for doc_type, info in self.get_document_status('travel').items():
                if doc_type in merged:
                    continue
                merged[doc_type] = info

        return merged


# ============================================================
# DOCUMENT REQUIREMENT (replaces the if/elif pyramid)
# ============================================================

class DocumentRequirement(models.Model):
    """
    Declares which documents are required for a given
    (profession, employment_basis, context).

    - Leave employment_basis blank to mean "any basis for this profession".
    - context='routine' → needed to trigger routine payment (salary/assignment/etc.)
    - context='travel'  → needed to claim DSA when traveling abroad
    """
    CONTEXT_CHOICES = [
        ('routine', 'Routine payment'),
        ('travel', 'Travel abroad (DSA claim)'),
    ]

    profession = models.CharField(
        max_length=50,
        choices=Personnel.PROFESSION_CHOICES,
    )
    employment_basis = models.CharField(
        max_length=20,
        choices=Personnel.EMPLOYMENT_BASIS_CHOICES,
        blank=True,
        help_text="Leave blank to apply to all employment bases for this profession.",
    )
    context = models.CharField(max_length=20, choices=CONTEXT_CHOICES, default='routine')
    document_type = models.CharField(max_length=50, choices=[
        ('passport', 'Passport Copy'),
        ('loa', 'Letter of Assignment (LOA)'),
        ('boarding_pass', 'Boarding Pass'),
        ('payment_claim', 'Payment Claim'),
        ('ticket', 'Ticket'),
        ('ticket_receipt', 'Ticket Receipt'),
        ('invoice', 'Invoice'),
        ('cp', 'Certificate of Performance'),
        ('ap', 'Authorization of Payment'),
        ('photo', 'Passport Photo'),
        ('other', 'Other'),
    ])
    is_required = models.BooleanField(default=True)

    class Meta:
        ordering = ['profession', 'employment_basis', 'context', 'document_type']
        unique_together = [['profession', 'employment_basis', 'context', 'document_type']]
        verbose_name = "Document Requirement"
        verbose_name_plural = "Document Requirements"

    def __str__(self):
        basis = self.employment_basis or 'any'
        return f"{self.profession}/{basis}/{self.context}: {self.document_type}"


# ============================================================
# DOCUMENT
# ============================================================

class Document(models.Model):
    DOCUMENT_TYPES = [
        ('passport', 'Passport Copy'),
        ('loa', 'Letter of Assignment (LOA)'),
        ('boarding_pass', 'Boarding Pass'),
        ('payment_claim', 'Payment Claim'),
        ('ticket', 'Ticket'),
        ('ticket_receipt', 'Ticket Receipt'),
        ('invoice', 'Invoice'),
        ('cp', 'Certificate of Performance'),
        ('ap', 'Authorization of Payment'),
        ('photo', 'Passport Photo'),
        ('other', 'Other'),
    ]

    # Shared display map for use by Personnel.get_document_type_display_names
    DISPLAY_NAMES = dict(DOCUMENT_TYPES)

    personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    file = models.FileField(
        upload_to='documents/%Y/%m/%d/',
        validators=[
            FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']),
            validate_file_size,
        ],
    )
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()
    mime_type = models.CharField(max_length=100)

    is_complete = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    verification_date = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)

    expiry_date = models.DateField(null=True, blank=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-upload_date']
        unique_together = ['personnel', 'document_type']

    def __str__(self):
        return f"{self.personnel.full_name()} - {self.get_document_type_display()}"

    def save(self, *args, **kwargs):
        if self.file:
            self.file_name = self.file.name
            self.file_size = self.file.size
            self.mime_type = self.file.file.content_type
        super().save(*args, **kwargs)


# ============================================================
# PAYMENT
# ============================================================

class Payment(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('submitted_to_finance', 'Submitted to Finance'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'USD'),
        ('EUR', 'EUR'),
        ('GHS', 'GHS'),
        ('TZS', 'TZS'),
    ]

    # NEW: what kind of payment this record represents
    PURPOSE_CHOICES = [
        ('salary', 'Monthly Salary'),
        ('assignment', 'Per-Assignment Payment'),
        ('daily', 'Daily / Per-Meeting Payment'),
        ('dsa', 'DSA (Travel Abroad)'),
        ('other', 'Other'),
    ]

    personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='payments')
    meeting = models.ForeignKey(Meeting, on_delete=models.SET_NULL, null=True, related_name='payments')

    purpose = models.CharField(
        max_length=20,
        choices=PURPOSE_CHOICES,
        default='dsa',
        help_text="What this payment is for: salary, assignment, daily, or DSA travel.",
    )

    role_type = models.CharField(max_length=50, choices=Personnel.PERSONNEL_TYPES)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    days_worked = models.IntegerField(default=2, validators=[MinValueValidator(1)])
    total_base = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    per_diem_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Per diem rate per day",
    )

    travel_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    accommodation_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    per_diem = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    special_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')

    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS, default='pending')
    finance_submission_date = models.DateTimeField(null=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.personnel.full_name()} - {self.total_amount} {self.currency} ({self.get_purpose_display()})"

    def calculate_totals(self):
        self.subtotal = (
            self.total_base
            + self.travel_allowance
            + self.accommodation_allowance
            + self.per_diem
            + self.special_allowance
        )
        self.tax = Decimal('0.00')
        self.total_amount = self.subtotal
        return self.total_amount

    def save(self, *args, **kwargs):
        self.calculate_totals()
        super().save(*args, **kwargs)


# ============================================================
# COMMUNICATION LOG
# ============================================================

class CommunicationLog(models.Model):
    COMMUNICATION_TYPES = [
        ('document_reminder', 'Document Reminder'),
        ('completion_notification', 'Completion Notification'),
        ('finance_submission', 'Finance Submission'),
        ('payment_notification', 'Payment Notification'),
        ('general', 'General'),
    ]

    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('opened', 'Opened'),
        ('bounced', 'Bounced'),
    ]

    personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='communications')
    communication_type = models.CharField(max_length=50, choices=COMMUNICATION_TYPES)
    subject = models.CharField(max_length=255)
    content = models.TextField()
    recipient_email = models.EmailField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    sent_date = models.DateTimeField(auto_now_add=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)

    error_message = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ['-sent_date']

    def __str__(self):
        return f"{self.personnel.full_name()} - {self.get_communication_type_display()} - {self.sent_date}"


# ============================================================
# NOTIFICATION TEMPLATE
# ============================================================

class NotificationTemplate(models.Model):
    TEMPLATE_TYPES = [
        ('document_reminder', 'Document Reminder'),
        ('completion_notification', 'Completion Notification'),
        ('finance_submission', 'Finance Submission'),
        ('payment_notification', 'Payment Notification'),
        ('welcome', 'Welcome'),
        ('general', 'General'),
    ]

    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES, unique=True)
    subject_template = models.CharField(max_length=255)
    body_template = models.TextField()
    html_template = models.TextField()

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.get_template_type_display()}"


# ============================================================
# UPLOAD HISTORY
# ============================================================

class UploadHistory(models.Model):
    personnel = models.ForeignKey('Personnel', on_delete=models.CASCADE, related_name='upload_history')
    document = models.ForeignKey('Document', on_delete=models.CASCADE, related_name='upload_history')
    uploaded_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-upload_date']

    def __str__(self):
        return f"{self.personnel.full_name()} - {self.document.document_type} - {self.upload_date}"


# ============================================================
# PAYMENT SETTINGS
# ============================================================

class PaymentSetting(models.Model):
    RATE_TYPES = [
        ('translator_regular_daily', 'Regular Translator - Daily Rate'),
        ('translator_regular_per_diem', 'Regular Translator - Per Diem (DSA)'),
        ('translator_staff_daily', 'Staff Translator - Daily Rate'),
        ('translator_staff_per_diem', 'Staff Translator - Per Diem (DSA)'),
        ('translator_online_word_rate', 'Online Translator - Rate per Word'),
        ('translator_freelance_daily', 'Translator Freelance - Daily Rate'),
        ('translator_freelance_per_diem', 'Translator Freelance - Per Diem (DSA)'),
        ('interpreter_regular_daily', 'Regular Interpreter - Daily Rate'),
        ('interpreter_regular_per_diem', 'Regular Interpreter - Per Diem (DSA)'),
        ('interpreter_staff_daily', 'Staff Interpreter - Daily Rate'),
        ('interpreter_staff_per_diem', 'Staff Interpreter - Per Diem (DSA)'),
        ('interpreter_daily_daily', 'Daily Interpreter - Daily Rate'),
        ('interpreter_freelance_daily', 'Interpreter Freelance - Daily Rate'),
        ('interpreter_freelance_per_diem', 'Interpreter Freelance - Per Diem (DSA)'),
        ('interpreter_freelance_accommodation', 'Interpreter Freelance - Accommodation'),
        ('interpreter_freelance_travel', 'Interpreter Freelance - Travel Allowance'),
        ('terminal_expenses', 'Terminal Expenses (Interpreter Freelance)'),
        ('visa_fee', 'Visa Fee (Interpreter Freelance)'),
        ('other_allowance', 'Other Allowance (Interpreter Freelance)'),
        ('standby_daily_rate', 'Standby Days - Daily Rate'),
        ('traveling_daily_rate', 'Traveling Days - Daily Rate'),
        ('air_ticket_base', 'Air Ticket - Base Rate'),
        ('air_ticket_ethiopia', 'Air Ticket - Ethiopia'),
        ('air_ticket_nairobi', 'Air Ticket - Nairobi/Kenya'),
        ('air_ticket_accra', 'Air Ticket - Accra/Ghana'),
        ('air_ticket_lome', 'Air Ticket - Lome/Togo'),
        ('air_ticket_long_distance', 'Air Ticket - Long Distance'),
        ('long_distance_travel_bonus', 'Long Distance Travel Bonus'),
    ]

    rate_type = models.CharField(max_length=50, choices=RATE_TYPES, unique=True)
    value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField(blank=True, help_text="Description of what this rate is for")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['rate_type']
        verbose_name = "Payment Setting"
        verbose_name_plural = "Payment Settings"

    def __str__(self):
        return f"{self.get_rate_type_display()}: {self.value}"

    @classmethod
    def get_value(cls, rate_type, default=Decimal('0.00')):
        try:
            setting = cls.objects.get(rate_type=rate_type, is_active=True)
            return setting.value
        except cls.DoesNotExist:
            return default

    @classmethod
    def get_all_rates(cls):
        rates = {}
        for setting in cls.objects.filter(is_active=True):
            rates[setting.rate_type] = setting.value
        return rates


# ============================================================
# DOCUMENT MERGE / MERGED DOCUMENT
# ============================================================

class DocumentMerge(models.Model):
    MERGE_FORMATS = [('pdf', 'PDF'), ('zip', 'ZIP Package')]
    MERGE_STATUS = [('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')]

    personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='document_merges')
    format = models.CharField(max_length=10, choices=MERGE_FORMATS)
    status = models.CharField(max_length=20, choices=MERGE_STATUS, default='pending')
    output_file = models.FileField(upload_to='merged_documents/%Y/%m/%d/', null=True, blank=True)
    file_size = models.IntegerField(null=True, blank=True)
    total_documents = models.IntegerField(default=0)
    missing_documents = models.JSONField(default=list)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Document Merge"
        verbose_name_plural = "Document Merges"

    def __str__(self):
        return f"{self.personnel.full_name()} - {self.format} - {self.created_at}"


class MergedDocument(models.Model):
    personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='merged_documents')
    pdf_file = models.FileField(upload_to='merged_documents/%Y/%m/%d/')
    file_size = models.IntegerField()
    total_documents = models.IntegerField(default=0)
    documents_included = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Merged Document"
        verbose_name_plural = "Merged Documents"

    def __str__(self):
        return f"{self.personnel.full_name()} - {self.created_at}"

    @classmethod
    def get_latest_for_personnel(cls, personnel):
        return cls.objects.filter(personnel=personnel).first()

    @classmethod
    def has_merged_document(cls, personnel):
        return cls.objects.filter(personnel=personnel).exists()


# ============================================================
# MEETING ASSIGNMENT
# ============================================================

class MeetingAssignment(models.Model):
    ROLE_CHOICES = [
        ('interpreter', 'Interpreter'),
        ('translator', 'Translator'),
        ('coordinator', 'Coordinator'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='meeting_assignment')
    personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='meeting_assignments')
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='assignments')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    username_for_meeting = models.CharField(max_length=150, unique=True)
    plain_password_hint = models.CharField(
        max_length=64, blank=True,
        help_text="Set only immediately after creation, cleared after email is sent.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    credentials_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [['personnel', 'meeting']]

    def __str__(self):
        return f"{self.personnel.full_name()} @ {self.meeting.name} ({self.role})"

    @staticmethod
    def generate_username(personnel, meeting):
        base = f"{personnel.first_name}.{personnel.last_name}".lower()
        base = ''.join(c for c in base if c.isalnum() or c == '.')
        candidate = f"{base}.mtg{meeting.id}"
        suffix = 1
        while User.objects.filter(username=candidate).exists():
            candidate = f"{base}.mtg{meeting.id}.{suffix}"
            suffix += 1
        return candidate

    @staticmethod
    def generate_password(length=10):
        alphabet = string.ascii_letters + string.digits
        alphabet = alphabet.replace('l', '').replace('I', '').replace('1', '').replace('O', '').replace('0', '')
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def role_from_personnel(self):
        prof = self.personnel.profession
        if prof == 'translator':
            return 'translator'
        if prof == 'interpreter':
            return 'interpreter'
        return 'coordinator'


# ============================================================
# AVAILABILITY REQUEST
# ============================================================

class AvailabilityRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending response'),
        ('available', 'Available — awaiting approval'),
        ('declined', 'Declined'),
        ('approved', 'Approved — credentials sent'),
        ('expired', 'Expired'),
    ]

    personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='availability_requests')
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='availability_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    responded_at = models.DateTimeField(null=True, blank=True)
    response_note = models.TextField(blank=True)

    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_availability_requests',
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    assignment = models.OneToOneField(
        'MeetingAssignment', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='availability_request',
    )

    invitation_sent_at = models.DateTimeField(null=True, blank=True)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [['personnel', 'meeting']]

    def __str__(self):
        return f"{self.personnel.full_name()} @ {self.meeting.name} — {self.get_status_display()}"

    def is_pending(self):
        return self.status == 'pending'

    def is_available(self):
        return self.status == 'available'

    def is_approved(self):
        return self.status == 'approved'


# ============================================================
# USER PROFILE
# ============================================================

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    must_change_password = models.BooleanField(default=False)
    password_changed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Profile({self.user.username})"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


# ============================================================
# CONTACT MESSAGE
# ============================================================

class ContactMessage(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('archived', 'Archived'),
    ]

    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    admin_notes = models.TextField(blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    replied_at = models.DateTimeField(null=True, blank=True)
    replied_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='contact_replies',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"{self.name} <{self.email}> — {self.subject}"
    

# personnel/models.py — add this model

# personnel/models.py — REPLACE the existing PersonnelExpense class

from django.db import models
from django.conf import settings
from decimal import Decimal


class PersonnelExpense(models.Model):
    """
    Manual expense entry for a Personnel — per meeting, per country.

    Rate-based fields (Salary, DSA, Travel Fee) are multiplied by
    `number_of_days` before being summed into the grand total.

    Flat fields (Standby, Terminal, Visa, Air Ticket, Other) are
    added directly.
    """
    CURRENCY_CHOICES = [
        ('USD', 'USD — US Dollar'),
        ('EUR', 'EUR — Euro'),
        ('ETB', 'ETB — Ethiopian Birr'),
        ('GBP', 'GBP — British Pound'),
    ]

    EXPENSE_CATEGORIES = [
        ('translator_group_i',   'Translator — Group I'),
        ('translator_group_ii',  'Translator — Group II'),
        ('translator_group_iii', 'Translator — Group III'),
        ('interpreter_group_i',  'Interpreter — Group I'),
        ('interpreter_group_ii', 'Interpreter — Group II'),
        ('interpreter_group_iii','Interpreter — Group III'),
        ('coordinator',          'Coordinator / Coordination Team'),
        ('other',                'Other'),
    ]

    # Relationships
    personnel = models.ForeignKey(
        'Personnel',
        on_delete=models.CASCADE,
        related_name='expenses',
    )
    meeting = models.ForeignKey(
        'Meeting',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='expenses',
    )

    # Categorisation
    country = models.CharField(max_length=100, blank=True,
                               help_text="Country / mission location for this rate")
    category = models.CharField(max_length=30, choices=EXPENSE_CATEGORIES,
                                default='other')
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='USD')

    # --- Rate multiplier ---
    number_of_days = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal('1.00'),
        help_text="Multiplier applied to Salary, DSA, and Travel Fee."
    )

    # --- Rate-based (multiplied by number_of_days) ---
    salary = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text="Per-day rate. Multiplied by number_of_days.",
    )
    dsa = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text="Per-day rate. Multiplied by number_of_days.",
    )
    travel_fee = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text="Per-day rate. Multiplied by number_of_days.",
    )

    # --- Flat amounts (added directly) ---
    standby_days = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        help_text="Total standby amount.",
    )
    terminal_expenses = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'))
    visa_fees = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'))
    air_ticket = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'))
    other = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'))

    # Computed + cached
    grand_total = models.DecimalField(
        max_digits=12, decimal_places=2,
        default=Decimal('0.00'), editable=False)

    # Admin lock
    is_locked = models.BooleanField(default=False,
        help_text="When locked, only admins can edit this expense record.")

    # Audit
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_expenses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Personnel Expense'
        verbose_name_plural = 'Personnel Expenses'
        indexes = [
            models.Index(fields=['personnel', '-created_at']),
            models.Index(fields=['meeting']),
            models.Index(fields=['is_locked']),
        ]

    def __str__(self):
        return (f"{self.personnel.full_name()} — {self.get_category_display()} "
                f"({self.currency} {self.grand_total})")

    # ---------- Calculations ----------
    @staticmethod
    def _safe_decimal(value):
        if value is None:
            return Decimal('0.00')
        try:
            return Decimal(str(value))
        except Exception:
            return Decimal('0.00')

    def compute_total(self):
        """
        Grand total =
            (salary + dsa + travel_fee) * number_of_days
            + standby_days
            + terminal_expenses
            + visa_fees
            + air_ticket
            + other
        """
        days = self._safe_decimal(self.number_of_days)
        if days <= 0:
            days = Decimal('1.00')  # safety: never multiply by zero or negative

        rate_based = (
            self._safe_decimal(self.salary)
            + self._safe_decimal(self.dsa)
            + self._safe_decimal(self.travel_fee)
        ) * days

        flat = (
            self._safe_decimal(self.standby_days)
            + self._safe_decimal(self.terminal_expenses)
            + self._safe_decimal(self.visa_fees)
            + self._safe_decimal(self.air_ticket)
            + self._safe_decimal(self.other)
        )

        return rate_based + flat

    def save(self, *args, **kwargs):
        # Ensure number_of_days is never zero or negative
        days = self._safe_decimal(self.number_of_days)
        if days <= 0:
            self.number_of_days = Decimal('1.00')

        # Server-side grand total
        self.grand_total = self.compute_total()
        super().save(*args, **kwargs)

    @property
    def rate_based_subtotal(self):
        """Sum of Salary + DSA + Travel Fee (per-day rates)."""
        return (self._safe_decimal(self.salary)
                + self._safe_decimal(self.dsa)
                + self._safe_decimal(self.travel_fee))

    @property
    def rate_based_total(self):
        """rate_based_subtotal × number_of_days."""
        days = self._safe_decimal(self.number_of_days) or Decimal('1.00')
        return self.rate_based_subtotal * days

    @property
    def flat_total(self):
        """Sum of flat amounts."""
        return (self._safe_decimal(self.standby_days)
                + self._safe_decimal(self.terminal_expenses)
                + self._safe_decimal(self.visa_fees)
                + self._safe_decimal(self.air_ticket)
                + self._safe_decimal(self.other))

    @property
    def line_items(self):
        """
        For templates / PDFs.
        Rate-based fields show their per-day rate AND the multiplied total.
        """
        days = self._safe_decimal(self.number_of_days) or Decimal('1.00')
        return [
            # label, per_day_rate, total
            ('Salary',           self.salary,           self._safe_decimal(self.salary) * days),
            ('DSA',              self.dsa,              self._safe_decimal(self.dsa) * days),
            ('Travel Fee',       self.travel_fee,       self._safe_decimal(self.travel_fee) * days),
            ('Standby',          None,                  self.standby_days),
            ('Terminal Expenses',None,                  self.terminal_expenses),
            ('Visa Fees',        None,                  self.visa_fees),
            ('Air Ticket',       None,                  self.air_ticket),
            ('Other',            None,                  self.other),
        ]
    # Add to PersonnelExpense
@property
def salary_total(self):
    return self._safe_decimal(self.salary) * (self._safe_decimal(self.number_of_days) or Decimal('1.00'))

@property
def dsa_total(self):
    return self._safe_decimal(self.dsa) * (self._safe_decimal(self.number_of_days) or Decimal('1.00'))

@property
def travel_fee_total(self):
    return self._safe_decimal(self.travel_fee) * (self._safe_decimal(self.number_of_days) or Decimal('1.00'))

class PersonnelMaster(models.Model):
    """
    Master list of personnel whose information can be pulled into
    the 'Add Personnel' form via a dropdown.
    """
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    first_name   = models.CharField(max_length=100, unique=True)
    middle_name  = models.CharField(max_length=100, blank=True)
    last_name    = models.CharField(max_length=100)
    gender       = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    nationality  = models.CharField(max_length=100)
    email        = models.EmailField()
    phone        = models.CharField(max_length=20)
    alternate_phone = models.CharField(max_length=20, blank=True)
    date_of_birth   = models.DateField(null=True, blank=True)
    city_departure  = models.CharField(max_length=200, blank=True)
    is_active       = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['first_name', 'last_name']
        verbose_name = "Personnel Master Record"
        verbose_name_plural = "Personnel Master List"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

# # 
# personnel/models.py

# # personnel/models.py

# from django.db import models
# from django.contrib.auth.models import User
# from django.utils import timezone
# from django.core.validators import FileExtensionValidator, MinValueValidator
# from django.core.exceptions import ValidationError
# import os
# from decimal import Decimal

# class Meeting(models.Model):
#     """Meeting/Event details"""
#     MEETING_STATUS = [
#         ('upcoming', 'Upcoming'),
#         ('ongoing', 'Ongoing'),
#         ('completed', 'Completed'),
#         ('cancelled', 'Cancelled'),
#     ]
    
#     name = models.CharField(max_length=200)
#     location = models.CharField(max_length=200)
#     start_date = models.DateField()
#     end_date = models.DateField()
#     status = models.CharField(max_length=20, choices=MEETING_STATUS, default='upcoming')
#     description = models.TextField(blank=True)
#     languages_required = models.JSONField(default=list)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     class Meta:
#         ordering = ['-start_date']
    
#     def __str__(self):
#         return f"{self.name} - {self.location}"
    
#     def days_duration(self):
#         return (self.end_date - self.start_date).days + 1


# def validate_photo_size(value):
#     """Validate photo file size"""
#     if value.size > 5 * 1024 * 1024:  # 5MB
#         raise ValidationError("Photo file size cannot exceed 5MB.")

# def validate_photo_extension(value):
#     """Validate photo file extension"""
#     ext = os.path.splitext(value.name)[1].lower()
#     valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
#     if ext not in valid_extensions:
#         raise ValidationError(f"Unsupported file extension. Allowed: {', '.join(valid_extensions)}")


# class Personnel(models.Model):
#     """Base model for both interpreters and translators"""
#     PERSONNEL_TYPES = [
#         ('interpreter', 'Interpreter'),
#         ('translator', 'Translator'),
#         ('icoordination', 'Interpretation coordination'),
#         ('Tcoordination', 'Translation coordination'),
#         ('adminassistant', 'Administrative Assistant'),
#         ('documentworkflowofficer', 'Document Workflow Officer'),
#         ('conferencesystemtechnitians', 'Conference System Technicians'),
#         ('documentationdistributionanandcirculation', 'Documentation Distribution and Circulation'),
#         ('documentationreproductionandprinting', 'Documentation Reproduction and Printing'),
#         ('both', 'Both'),
#     ]
    
#     TRANSLATOR_TYPES = [
#         ('freelance', 'Freelance Translator'),
#         ('staff', 'Staff Translator'),
#     ]
    
#     INTERPRETER_TYPES = [
#         ('freelance', 'Freelance Interpreter'),
#         ('staff', 'Staff Interpreter'),
#     ]
    
#     GENDER_CHOICES = [
#         ('M', 'Male'),
#         ('F', 'Female'),
#     ]
    
#     # Personal Information
#     first_name = models.CharField(max_length=100)
#     last_name = models.CharField(max_length=100)
#     middle_name = models.CharField(max_length=100, blank=True)
#     gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
#     nationality = models.CharField(max_length=100)
#     date_of_birth = models.DateField(null=True, blank=True)
#     email = models.EmailField()
#     phone = models.CharField(max_length=20)
#     alternative_phone = models.CharField(max_length=20, blank=True)
    
#     # Professional Information
#     personnel_type = models.CharField(max_length=50, choices=PERSONNEL_TYPES, default='interpreter')
#     translator_type = models.CharField(
#         max_length=20, 
#         choices=TRANSLATOR_TYPES, 
#         blank=True, 
#         null=True,
#         help_text="Required only for translators: Freelance or Staff"
#     )
#     interpreter_type = models.CharField(
#         max_length=20, 
#         choices=INTERPRETER_TYPES, 
#         blank=True, 
#         null=True,
#         help_text="Required only for interpreters: Freelance or Staff"
#     )
#     photo = models.ImageField(
#         upload_to='personnel_photos/%Y/%m/%d/',
#         null=True,
#         blank=True,
#         validators=[validate_photo_extension, validate_photo_size],
#         help_text="Upload a passport-style photo (JPG, PNG, GIF - max 5MB)"
#     )
#     designation = models.CharField(max_length=100, default='INTERPRETER')
#     city_departure = models.CharField(max_length=200)
#     languages = models.JSONField(default=list)
    
#     # Assignment Details
#     meeting = models.ForeignKey(Meeting, on_delete=models.SET_NULL, null=True, related_name='personnel')
#     is_active = models.BooleanField(default=True)
#     documents_complete = models.BooleanField(default=False)
    
#     # Additional Information
#     notes = models.TextField(blank=True)
#     emergency_contact_name = models.CharField(max_length=100, blank=True)
#     emergency_contact_phone = models.CharField(max_length=20, blank=True)
    
#     # Timestamps
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_personnel')
    
#     class Meta:
#         ordering = ['last_name', 'first_name']
#         indexes = [
#             models.Index(fields=['email']),
#             models.Index(fields=['personnel_type']),
#             models.Index(fields=['documents_complete']),
#         ]
    
#     def __str__(self):
#         return f"{self.first_name} {self.last_name} - {self.get_personnel_type_display()}"
    
#     def full_name(self):
#         if self.middle_name:
#             return f"{self.first_name} {self.middle_name} {self.last_name}"
#         return f"{self.first_name} {self.last_name}"
    
#     # ================================================================
#     # DOCUMENT METHODS - These must be at the same indentation level
#     # ================================================================
    
#     def get_required_documents(self):
#         """
#         Get required documents based on personnel type and subtype
        
#         Requirements:
#         - Freelance Translator: LOA, Payment Claim, Invoice
#         - Staff Translator: Passport, Boarding Pass, Ticket
#         - Freelance Interpreter: Passport, LOA, Payment Claim, Ticket, Ticket Receipt, Boarding Pass
#         - Staff Interpreter: Passport, Boarding Pass, Ticket, Ticket Receipt
#         - Other types: Passport, Boarding Pass, Ticket, Ticket Receipt
#         """
        
#         # For Translators
#         if self.personnel_type == 'translator':
#             if self.translator_type == 'freelance':
#                 return ['loa', 'payment_claim', 'invoice']
#             elif self.translator_type == 'staff':
#                 return ['passport', 'boarding_pass', 'ticket']
#             else:
#                 return ['loa', 'payment_claim', 'invoice']
        
#         # For Interpreters
#         elif self.personnel_type == 'interpreter':
#             if self.interpreter_type == 'freelance':
#                 return ['passport', 'loa', 'payment_claim', 'ticket', 'ticket_receipt', 'boarding_pass']
#             elif self.interpreter_type == 'staff':
#                 return ['passport', 'boarding_pass', 'ticket', 'ticket_receipt']
#             else:
#                 # Default for interpreters
#                 return ['passport', 'boarding_pass', 'ticket', 'ticket_receipt']
        
#         # For Translation coordination
#         elif self.personnel_type == 'Tcoordination':
#             return ['passport', 'boarding_pass', 'ticket', 'ticket_receipt']
        
#         # For Interpretation coordination
#         elif self.personnel_type == 'icoordination':
#             return ['passport', 'boarding_pass', 'ticket', 'ticket_receipt']
        
#         # For all other types
#         else:
#             return ['passport', 'boarding_pass', 'ticket', 'ticket_receipt']

#     def get_document_type_display_names(self):
#         """Get display names for required documents"""
#         doc_map = {
#             'passport': 'Passport Copy',
#             'loa': 'Letter of Assignment (LOA)',
#             'boarding_pass': 'Boarding Pass',
#             'payment_claim': 'Payment Claim',
#             'ticket': 'Ticket',
#             'ticket_receipt': 'Ticket Receipt',
#             'invoice': 'Invoice',
#             'other': 'Other',
#         }
#         required_docs = self.get_required_documents()
#         return {doc: doc_map.get(doc, doc.title()) for doc in required_docs}

#     def get_missing_documents(self):
#         """Get missing documents based on personnel type"""
#         required_docs = self.get_required_documents()
#         uploaded_docs = self.documents.filter(is_complete=True).values_list('document_type', flat=True)
#         return [doc for doc in required_docs if doc not in uploaded_docs]

#     def has_all_documents(self):
#         """Check if all required documents are uploaded"""
#         return len(self.get_missing_documents()) == 0

#     def get_document_status(self):
#         """Get status of all required documents"""
#         documents = self.documents.all()
#         required_docs = self.get_required_documents()
#         status = {}
        
#         for doc_type in required_docs:
#             doc = documents.filter(document_type=doc_type).first()
#             status[doc_type] = {
#                 'uploaded': doc is not None,
#                 'verified': doc.is_verified if doc else False,
#                 'upload_date': doc.upload_date if doc else None,
#                 'file_name': doc.file_name if doc else None,
#             }
#         return status


# def validate_file_size(value):
#     filesize = value.size
#     if filesize > 5242880:  # 5MB
#         raise ValidationError("Maximum file size is 5MB")


# class Document(models.Model):
#     DOCUMENT_TYPES = [
#         ('passport', 'Passport Copy'),
#         ('loa', 'Letter of Assignment (LOA)'),
#         ('boarding_pass', 'Boarding Pass'),
#         ('payment_claim', 'Payment Claim'),
#         ('ticket', 'Ticket'),
#         ('ticket_receipt', 'Ticket Receipt'),
#         ('invoice', 'Invoice'),
#         ('photo', 'Passport Photo'),
#         ('other', 'Other'),
#     ]
    
#     personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='documents')
#     document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
#     file = models.FileField(
#         upload_to='documents/%Y/%m/%d/',
#         validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']), validate_file_size]
#     )
#     file_name = models.CharField(max_length=255)
#     file_size = models.IntegerField()
#     mime_type = models.CharField(max_length=100)
    
#     is_complete = models.BooleanField(default=True)
#     is_verified = models.BooleanField(default=False)
#     verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
#     verification_date = models.DateTimeField(null=True, blank=True)
#     verification_notes = models.TextField(blank=True)
    
#     expiry_date = models.DateField(null=True, blank=True)
#     upload_date = models.DateTimeField(auto_now_add=True)
#     notes = models.TextField(blank=True)
    
#     class Meta:
#         ordering = ['-upload_date']
#         unique_together = ['personnel', 'document_type']
    
#     def __str__(self):
#         return f"{self.personnel.full_name()} - {self.get_document_type_display()}"
    
#     def save(self, *args, **kwargs):
#         if self.file:
#             self.file_name = self.file.name
#             self.file_size = self.file.size
#             self.mime_type = self.file.file.content_type
#         super().save(*args, **kwargs)


# # ... rest of your models (Payment, CommunicationLog, etc.) ...


# # class Payment(models.Model):
# #     PAYMENT_STATUS = [
# #         ('pending', 'Pending'),
# #         ('submitted_to_finance', 'Submitted to Finance'),
# #         ('approved', 'Approved'),
# #         ('paid', 'Paid'),
# #         ('rejected', 'Rejected'),
# #     ]
    
# #     CURRENCY_CHOICES = [
# #         ('USD', 'USD'),
# #         ('EUR', 'EUR'),
# #         ('GHS', 'GHS'),
# #         ('TZS', 'TZS'),
# #     ]
    
# #     personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='payments')
# #     meeting = models.ForeignKey(Meeting, on_delete=models.SET_NULL, null=True, related_name='payments')
    
# #     role_type = models.CharField(max_length=50, choices=Personnel.PERSONNEL_TYPES)
# #     daily_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
# #     days_worked = models.IntegerField(default=2, validators=[MinValueValidator(1)])
# #     total_base = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
# #     travel_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
# #     accommodation_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
# #     per_diem = models.DecimalField(max_digits=10, decimal_places=2, default=0)
# #     special_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
# #     subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
# #     tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
# #     total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
# #     currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    
# #     payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS, default='pending')
# #     finance_submission_date = models.DateTimeField(null=True, blank=True)
# #     payment_date = models.DateTimeField(null=True, blank=True)
# #     payment_reference = models.CharField(max_length=100, blank=True)
    
# #     notes = models.TextField(blank=True)
# #     created_at = models.DateTimeField(auto_now_add=True)
# #     updated_at = models.DateTimeField(auto_now=True)
# #     processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
# #     class Meta:
# #         ordering = ['-created_at']
    
# #     def __str__(self):
# #         return f"{self.personnel.full_name()} - {self.total_amount} {self.currency}"
    
# #     def calculate_totals(self):
# #         """Calculate all totals using Decimal arithmetic - NO TAX"""
# #         self.subtotal = (
# #             self.total_base +
# #             self.travel_allowance +
# #             self.accommodation_allowance +
# #             self.per_diem +
# #             self.special_allowance
# #         )
# #         # NO TAX - tax is always 0
# #         self.tax = Decimal('0.00')
# #         self.total_amount = self.subtotal
# #         return self.total_amount
    
# #     def save(self, *args, **kwargs):
# #         self.calculate_totals()
# #         super().save(*args, **kwargs)

# # personnel/models.py - Payment class

# # personnel/models.py - Update Payment model

# class Payment(models.Model):
#     PAYMENT_STATUS = [
#         ('pending', 'Pending'),
#         ('submitted_to_finance', 'Submitted to Finance'),
#         ('approved', 'Approved'),
#         ('paid', 'Paid'),
#         ('rejected', 'Rejected'),
#     ]
    
#     CURRENCY_CHOICES = [
#         ('USD', 'USD'),
#         ('EUR', 'EUR'),
#         ('GHS', 'GHS'),
#         ('TZS', 'TZS'),
#     ]
    
#     personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='payments')
#     meeting = models.ForeignKey(Meeting, on_delete=models.SET_NULL, null=True, related_name='payments')
    
#     role_type = models.CharField(max_length=50, choices=Personnel.PERSONNEL_TYPES)
#     daily_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     days_worked = models.IntegerField(default=2, validators=[MinValueValidator(1)])
#     total_base = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
#     # Add this field to store the per diem rate separately
#     per_diem_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0, 
#                                         help_text="Per diem rate per day")
    
#     travel_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     accommodation_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     per_diem = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Total per diem (rate × days)
#     special_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
#     subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    
#     payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS, default='pending')
#     finance_submission_date = models.DateTimeField(null=True, blank=True)
#     payment_date = models.DateTimeField(null=True, blank=True)
#     payment_reference = models.CharField(max_length=100, blank=True)
    
#     notes = models.TextField(blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
#     class Meta:
#         ordering = ['-created_at']
    
#     def __str__(self):
#         return f"{self.personnel.full_name()} - {self.total_amount} {self.currency}"
    
#     def calculate_totals(self):
#         """
#         Calculate all totals using Decimal arithmetic.
#         NO TAX - tax is always 0.
#         """
#         self.subtotal = (
#             self.total_base +
#             self.travel_allowance +
#             self.accommodation_allowance +
#             self.per_diem +  # This is already rate × days
#             self.special_allowance
#         )
#         # IMPORTANT: Tax is always 0 - no tax applied
#         self.tax = Decimal('0.00')
#         self.total_amount = self.subtotal
#         return self.total_amount
    
#     def save(self, *args, **kwargs):
#         self.calculate_totals()
#         super().save(*args, **kwargs)



# class CommunicationLog(models.Model):
#     COMMUNICATION_TYPES = [
#         ('document_reminder', 'Document Reminder'),
#         ('completion_notification', 'Completion Notification'),
#         ('finance_submission', 'Finance Submission'),
#         ('payment_notification', 'Payment Notification'),
#         ('general', 'General'),
#     ]
    
#     STATUS_CHOICES = [
#         ('sent', 'Sent'),
#         ('failed', 'Failed'),
#         ('opened', 'Opened'),
#         ('bounced', 'Bounced'),
#     ]
    
#     personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='communications')
#     communication_type = models.CharField(max_length=50, choices=COMMUNICATION_TYPES)
#     subject = models.CharField(max_length=255)
#     content = models.TextField()
#     recipient_email = models.EmailField()
    
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
#     sent_date = models.DateTimeField(auto_now_add=True)
#     opened_at = models.DateTimeField(null=True, blank=True)
#     clicked_at = models.DateTimeField(null=True, blank=True)
    
#     error_message = models.TextField(blank=True)
#     notes = models.TextField(blank=True)
#     metadata = models.JSONField(default=dict)
    
#     class Meta:
#         ordering = ['-sent_date']
    
#     def __str__(self):
#         return f"{self.personnel.full_name()} - {self.get_communication_type_display()} - {self.sent_date}"


# class NotificationTemplate(models.Model):
#     TEMPLATE_TYPES = [
#         ('document_reminder', 'Document Reminder'),
#         ('completion_notification', 'Completion Notification'),
#         ('finance_submission', 'Finance Submission'),
#         ('payment_notification', 'Payment Notification'),
#         ('welcome', 'Welcome'),
#         ('general', 'General'),
#     ]
    
#     name = models.CharField(max_length=100)
#     template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES, unique=True)
#     subject_template = models.CharField(max_length=255)
#     body_template = models.TextField()
#     html_template = models.TextField()
    
#     is_active = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     def __str__(self):
#         return f"{self.name} - {self.get_template_type_display()}"
    

# class UploadHistory(models.Model):
#     """Track document upload history"""
#     personnel = models.ForeignKey('Personnel', on_delete=models.CASCADE, related_name='upload_history')
#     document = models.ForeignKey('Document', on_delete=models.CASCADE, related_name='upload_history')
#     uploaded_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
#     upload_date = models.DateTimeField(auto_now_add=True)
#     ip_address = models.GenericIPAddressField(null=True, blank=True)
#     user_agent = models.TextField(blank=True)
#     notes = models.TextField(blank=True)

#     class Meta:
#         ordering = ['-upload_date']

#     def __str__(self):
#         return f"{self.personnel.full_name()} - {self.document.document_type} - {self.upload_date}"
    

# # personnel/models.py - Add this new model

# class PaymentSetting(models.Model):
#     """Store payment rate settings that can be configured by admins"""
    
#     # Rate categories
#     RATE_TYPES = [
#         ('translator_freelance_daily', 'Translator Freelance - Daily Rate'),
#         ('translator_freelance_per_diem', 'Translator Freelance - Per Diem (DSA)'),
#         ('translator_staff_daily', 'Translator Staff - Daily Rate'),
#         ('translator_staff_per_diem', 'Translator Staff - Per Diem (DSA)'),
#         ('interpreter_freelance_daily', 'Interpreter Freelance - Daily Rate'),
#         ('interpreter_freelance_per_diem', 'Interpreter Freelance - Per Diem (DSA)'),
#         ('interpreter_freelance_accommodation', 'Interpreter Freelance - Accommodation'),
#         ('interpreter_freelance_travel', 'Interpreter Freelance - Travel Allowance'),
#         ('interpreter_staff_daily', 'Interpreter Staff - Daily Rate'),
#         ('interpreter_staff_per_diem', 'Interpreter Staff - Per Diem (DSA)'),
#         ('terminal_expenses', 'Terminal Expenses (Interpreter Freelance)'),
#         ('visa_fee', 'Visa Fee (Interpreter Freelance)'),
#         ('other_allowance', 'Other Allowance (Interpreter Freelance)'),
#         ('standby_daily_rate', 'Standby Days - Daily Rate'),
#         ('traveling_daily_rate', 'Traveling Days - Daily Rate'),
#         ('air_ticket_base', 'Air Ticket - Base Rate'),
#         ('air_ticket_ethiopia', 'Air Ticket - Ethiopia'),
#         ('air_ticket_nairobi', 'Air Ticket - Nairobi/Kenya'),
#         ('air_ticket_accra', 'Air Ticket - Accra/Ghana'),
#         ('air_ticket_lome', 'Air Ticket - Lome/Togo'),
#         ('air_ticket_long_distance', 'Air Ticket - Long Distance'),
#         ('long_distance_travel_bonus', 'Long Distance Travel Bonus'),
#     ]
    
#     rate_type = models.CharField(max_length=50, choices=RATE_TYPES, unique=True)
#     value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     description = models.TextField(blank=True, help_text="Description of what this rate is for")
#     is_active = models.BooleanField(default=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
#     class Meta:
#         ordering = ['rate_type']
#         verbose_name = "Payment Setting"
#         verbose_name_plural = "Payment Settings"
    
#     def __str__(self):
#         return f"{self.get_rate_type_display()}: {self.value}"
    
#     @classmethod
#     def get_value(cls, rate_type, default=Decimal('0.00')):
#         """Get a rate value by type with default fallback"""
#         try:
#             setting = cls.objects.get(rate_type=rate_type, is_active=True)
#             return setting.value
#         except cls.DoesNotExist:
#             return default
    
#     @classmethod
#     def get_all_rates(cls):
#         """Get all rates as a dictionary"""
#         rates = {}
#         for setting in cls.objects.filter(is_active=True):
#             rates[setting.rate_type] = setting.value
#         return rates
    
# # personnel/models.py - Add this new model

# class DocumentMerge(models.Model):
#     """Track document merge operations"""
#     MERGE_FORMATS = [
#         ('pdf', 'PDF'),
#         ('zip', 'ZIP Package'),
#     ]
    
#     MERGE_STATUS = [
#         ('pending', 'Pending'),
#         ('completed', 'Completed'),
#         ('failed', 'Failed'),
#     ]
    
#     personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='document_merges')
#     format = models.CharField(max_length=10, choices=MERGE_FORMATS)
#     status = models.CharField(max_length=20, choices=MERGE_STATUS, default='pending')
#     output_file = models.FileField(upload_to='merged_documents/%Y/%m/%d/', null=True, blank=True)
#     file_size = models.IntegerField(null=True, blank=True)
#     total_documents = models.IntegerField(default=0)
#     missing_documents = models.JSONField(default=list)
#     error_message = models.TextField(blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     completed_at = models.DateTimeField(null=True, blank=True)
#     created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
#     class Meta:
#         ordering = ['-created_at']
#         verbose_name = "Document Merge"
#         verbose_name_plural = "Document Merges"
    
#     def __str__(self):
#         return f"{self.personnel.full_name()} - {self.format} - {self.created_at}"
    

# # personnel/models.py - Add this model if not already present

# class MergedDocument(models.Model):
#     """Track merged PDF documents for personnel"""
#     personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='merged_documents')
#     pdf_file = models.FileField(upload_to='merged_documents/%Y/%m/%d/')
#     file_size = models.IntegerField()
#     total_documents = models.IntegerField(default=0)
#     documents_included = models.JSONField(default=list)
#     created_at = models.DateTimeField(auto_now_add=True)
#     created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
#     class Meta:
#         ordering = ['-created_at']
#         verbose_name = "Merged Document"
#         verbose_name_plural = "Merged Documents"
    
#     def __str__(self):
#         return f"{self.personnel.full_name()} - {self.created_at}"
    
#     @classmethod
#     def get_latest_for_personnel(cls, personnel):
#         """Get the latest merged document for a personnel"""
#         return cls.objects.filter(personnel=personnel).first()
    
#     @classmethod
#     def has_merged_document(cls, personnel):
#         """Check if a personnel has a merged document"""
#         return cls.objects.filter(personnel=personnel).exists()
    
# # personnel/models.py — append at the end

# import secrets
# import string


# class MeetingAssignment(models.Model):
#     """
#     Links an authenticated user to a Personnel record for a specific meeting.
#     One user per personnel-meeting pair. Created when admin demands availability.
#     """
#     ROLE_CHOICES = [
#         ('interpreter', 'Interpreter'),
#         ('translator', 'Translator'),
#         ('coordinator', 'Coordinator'),
#     ]

#     user = models.OneToOneField(
#         User,
#         on_delete=models.CASCADE,
#         related_name='meeting_assignment'
#     )
#     personnel = models.ForeignKey(
#         Personnel,
#         on_delete=models.CASCADE,
#         related_name='meeting_assignments'
#     )
#     meeting = models.ForeignKey(
#         Meeting,
#         on_delete=models.CASCADE,
#         related_name='assignments'
#     )
#     role = models.CharField(max_length=20, choices=ROLE_CHOICES)
#     username_for_meeting = models.CharField(max_length=150, unique=True)
#     plain_password_hint = models.CharField(
#         max_length=64, blank=True,
#         help_text="Set only immediately after creation, cleared after email is sent."
#     )
#     created_at = models.DateTimeField(auto_now_add=True)
#     is_active = models.BooleanField(default=True)
#     credentials_sent_at = models.DateTimeField(null=True, blank=True)

#     class Meta:
#         ordering = ['-created_at']
#         unique_together = [['personnel', 'meeting']]

#     def __str__(self):
#         return f"{self.personnel.full_name()} @ {self.meeting.name} ({self.role})"

#     @staticmethod
#     def generate_username(personnel, meeting):
#         """Generate a unique username like john.doe.mtg26"""
#         base = f"{personnel.first_name}.{personnel.last_name}".lower()
#         base = ''.join(c for c in base if c.isalnum() or c == '.')
#         candidate = f"{base}.mtg{meeting.id}"
#         suffix = 1
#         while User.objects.filter(username=candidate).exists():
#             candidate = f"{base}.mtg{meeting.id}.{suffix}"
#             suffix += 1
#         return candidate

#     @staticmethod
#     def generate_password(length=10):
#         """Generate a readable random password"""
#         alphabet = string.ascii_letters + string.digits
#         # avoid ambiguous characters
#         alphabet = alphabet.replace('l', '').replace('I', '').replace('1', '').replace('O', '').replace('0', '')
#         return ''.join(secrets.choice(alphabet) for _ in range(length))

#     def role_from_personnel(self):
#         """Map personnel_type to a role string"""
#         pt = self.personnel.personnel_type
#         if pt == 'translator':
#             return 'translator'
#         if pt == 'interpreter':
#             return 'interpreter'
#         return 'coordinator'
    
# # personnel/models.py — append

# class AvailabilityRequest(models.Model):
#     """
#     Tracks availability inquiry and approval for each person nominated for a meeting.
#     """
#     STATUS_CHOICES = [
#         ('pending', 'Pending response'),
#         ('available', 'Available — awaiting approval'),
#         ('declined', 'Declined'),
#         ('approved', 'Approved — credentials sent'),
#         ('expired', 'Expired'),
#     ]

#     personnel = models.ForeignKey(
#         Personnel,
#         on_delete=models.CASCADE,
#         related_name='availability_requests'
#     )
#     meeting = models.ForeignKey(
#         Meeting,
#         on_delete=models.CASCADE,
#         related_name='availability_requests'
#     )
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

#     # Response
#     responded_at = models.DateTimeField(null=True, blank=True)
#     response_note = models.TextField(blank=True)

#     # Approval
#     approved_by = models.ForeignKey(
#         User, on_delete=models.SET_NULL, null=True, blank=True,
#         related_name='approved_availability_requests'
#     )
#     approved_at = models.DateTimeField(null=True, blank=True)

#     # Link to credentials (only after approval)
#     assignment = models.OneToOneField(
#         'MeetingAssignment',
#         on_delete=models.SET_NULL,
#         null=True, blank=True,
#         related_name='availability_request'
#     )

#     # Email tracking
#     invitation_sent_at = models.DateTimeField(null=True, blank=True)
#     reminder_sent_at = models.DateTimeField(null=True, blank=True)

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         ordering = ['-created_at']
#         unique_together = [['personnel', 'meeting']]

#     def __str__(self):
#         return f"{self.personnel.full_name()} @ {self.meeting.name} — {self.get_status_display()}"

#     def is_pending(self):
#         return self.status == 'pending'

#     def is_available(self):
#         return self.status == 'available'

#     def is_approved(self):
#         return self.status == 'approved'
    

# from django.db.models.signals import post_save
# from django.dispatch import receiver


# class UserProfile(models.Model):
#     """Extends the built-in User with app-specific flags."""
#     user = models.OneToOneField(
#         User,
#         on_delete=models.CASCADE,
#         related_name='profile',
#     )
#     must_change_password = models.BooleanField(default=False)
#     password_changed_at = models.DateTimeField(null=True, blank=True)

#     def __str__(self):
#         return f"Profile({self.user.username})"


# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         UserProfile.objects.get_or_create(user=instance)


# # personnel/models.py — append

# class ContactMessage(models.Model):
#     """Messages submitted through the public Contact Us form."""
#     STATUS_CHOICES = [
#         ('new', 'New'),
#         ('read', 'Read'),
#         ('replied', 'Replied'),
#         ('archived', 'Archived'),
#     ]

#     name = models.CharField(max_length=150)
#     email = models.EmailField()
#     phone = models.CharField(max_length=30, blank=True)
#     subject = models.CharField(max_length=200)
#     message = models.TextField()

#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
#     admin_notes = models.TextField(blank=True)

#     ip_address = models.GenericIPAddressField(null=True, blank=True)
#     user_agent = models.TextField(blank=True)

#     created_at = models.DateTimeField(auto_now_add=True)
#     replied_at = models.DateTimeField(null=True, blank=True)
#     replied_by = models.ForeignKey(
#         User, on_delete=models.SET_NULL, null=True, blank=True,
#         related_name='contact_replies'
#     )

#     class Meta:
#         ordering = ['-created_at']
#         verbose_name = "Contact Message"
#         verbose_name_plural = "Contact Messages"

#     def __str__(self):
#         return f"{self.name} <{self.email}> — {self.subject}"