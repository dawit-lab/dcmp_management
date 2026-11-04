# personnel/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.core.exceptions import ValidationError
import os
from decimal import Decimal

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


class Personnel(models.Model):
    """Base model for both interpreters and translators"""
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
    
    # Professional Information
    personnel_type = models.CharField(max_length=50, choices=PERSONNEL_TYPES, default='interpreter')
    translator_type = models.CharField(
        max_length=20, 
        choices=TRANSLATOR_TYPES, 
        blank=True, 
        null=True,
        help_text="Required only for translators: Freelance or Staff"
    )
    designation = models.CharField(max_length=100, default='INTERPRETER')
    city_departure = models.CharField(max_length=200)
    languages = models.JSONField(default=list)
    
    # Assignment Details
    meeting = models.ForeignKey(Meeting, on_delete=models.SET_NULL, null=True, related_name='personnel')
    is_active = models.BooleanField(default=True)
    documents_complete = models.BooleanField(default=False)
    
    # Additional Information
    notes = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_personnel')
    
    class Meta:
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['personnel_type']),
            models.Index(fields=['documents_complete']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_personnel_type_display()}"
    
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    # ================================================================
    # DOCUMENT METHODS - These MUST be indented inside the class
    # ================================================================
    
    def get_required_documents(self):
        """
        Get required documents based on personnel type and translator type
        
        Requirements:
        - Freelance Translator: LOA, Payment Claim, Invoice
        - Staff Translator: Passport Copy, Boarding Pass, Ticket
        - Interpreter: LOA, Payment Claim, Ticket, Ticket Receipt, Passport Copy, Boarding Pass
        - Translation coordination (Tcoordination): Passport Copy, Boarding Pass, Ticket, Ticket Receipt
        - Interpretation coordination (icoordination): Passport Copy, Boarding Pass, Ticket, Ticket Receipt
        - Other types: Passport Copy, Boarding Pass, Ticket, Ticket Receipt
        """
        
        # For Translators
        if self.personnel_type == 'translator':
            if self.translator_type == 'freelance':
                return ['loa', 'payment_claim', 'invoice']
            elif self.translator_type == 'staff':
                return ['passport', 'boarding_pass', 'ticket']
            else:
                return ['loa', 'payment_claim', 'invoice']
        
        # For Interpreters
        elif self.personnel_type == 'interpreter':
            return ['loa', 'payment_claim', 'ticket', 'ticket_receipt', 'passport', 'boarding_pass']
        
        # For Translation coordination
        elif self.personnel_type == 'Tcoordination':
            return ['passport', 'boarding_pass', 'ticket', 'ticket_receipt']
        
        # For Interpretation coordination
        elif self.personnel_type == 'icoordination':
            return ['passport', 'boarding_pass', 'ticket', 'ticket_receipt']
        
        # For all other types
        else:
            return ['passport', 'boarding_pass', 'ticket', 'ticket_receipt']
    
    def get_document_type_display_names(self):
        """Get display names for required documents"""
        doc_map = {
            'passport': 'Passport Copy',
            'loa': 'Letter of Assignment (LOA)',
            'boarding_pass': 'Boarding Pass',
            'payment_claim': 'Payment Claim',
            'ticket': 'Ticket',
            'ticket_receipt': 'Ticket Receipt',
            'invoice': 'Invoice',
            'other': 'Other',
        }
        required_docs = self.get_required_documents()
        return {doc: doc_map.get(doc, doc.title()) for doc in required_docs}
    
    def get_missing_documents(self):
        """Get missing documents based on personnel type"""
        required_docs = self.get_required_documents()
        uploaded_docs = self.documents.filter(is_complete=True).values_list('document_type', flat=True)
        return [doc for doc in required_docs if doc not in uploaded_docs]
    
    def has_all_documents(self):
        """Check if all required documents are uploaded"""
        return len(self.get_missing_documents()) == 0
    
    def get_document_status(self):
        """Get status of all required documents"""
        documents = self.documents.all()
        required_docs = self.get_required_documents()
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


def validate_file_size(value):
    filesize = value.size
    if filesize > 5242880:  # 5MB
        raise ValidationError("Maximum file size is 5MB")


class Document(models.Model):
    DOCUMENT_TYPES = [
        ('passport', 'Passport Copy'),
        ('loa', 'Letter of Assignment (LOA)'),
        ('boarding_pass', 'Boarding Pass'),
        ('payment_claim', 'Payment Claim'),
        ('ticket', 'Ticket'),
        ('ticket_receipt', 'Ticket Receipt'),
        ('invoice', 'Invoice'),
        ('other', 'Other'),
    ]
    
    personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    file = models.FileField(
        upload_to='documents/%Y/%m/%d/',
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']), validate_file_size]
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
    
    personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='payments')
    meeting = models.ForeignKey(Meeting, on_delete=models.SET_NULL, null=True, related_name='payments')
    
    role_type = models.CharField(max_length=50, choices=Personnel.PERSONNEL_TYPES)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    days_worked = models.IntegerField(default=2, validators=[MinValueValidator(1)])
    total_base = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
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
        return f"{self.personnel.full_name()} - {self.total_amount} {self.currency}"
    
    def calculate_totals(self):
        """Calculate all totals using Decimal arithmetic."""
        self.subtotal = (
            self.total_base +
            self.travel_allowance +
            self.accommodation_allowance +
            self.per_diem +
            self.special_allowance
        )
        self.tax = self.subtotal * Decimal('0.05')
        self.total_amount = self.subtotal + self.tax
        return self.total_amount
    
    def save(self, *args, **kwargs):
        self.calculate_totals()
        super().save(*args, **kwargs)


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
    

class UploadHistory(models.Model):
    """Track document upload history"""
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