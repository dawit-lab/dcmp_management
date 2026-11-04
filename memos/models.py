from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError

class Department(models.Model):
    """Department that sends or receives memos"""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class MemoType(models.Model):
    """Types of memos"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class MemoCategory(models.Model):
    """Categories for memos"""
    CATEGORY_TYPES = [
        ('interpreter_nomination', 'Interpreter Nomination'),
        ('translator_nomination', 'Translator Nomination'),
        ('both_nomination', 'Both Interpreter & Translator Nomination'),
        ('interpreter_list', 'Interpreter List Preparation'),
        ('translator_list', 'Translator List Preparation'),
        ('both_list', 'Both Interpreter & Translator List Preparation'),
        ('general_request', 'General Request'),
        ('information', 'Information'),
        ('circular', 'Circular'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=50, choices=CATEGORY_TYPES, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Memo(models.Model):
    """Main Memo model for incoming and outgoing memos"""
    MEMO_DIRECTION = [
        ('incoming', 'Incoming'),
        ('outgoing', 'Outgoing'),
    ]
    
    MEMO_STATUS = [
        ('draft', 'Draft'),
        ('registered', 'Registered'),
        ('dispatched', 'Dispatched'),
        ('received', 'Received'),
        ('in_progress', 'In Progress'),
        ('response_required', 'Response Required'),
        ('response_prepared', 'Response Prepared'),
        ('response_approved', 'Response Approved'),
        ('response_sent', 'Response Sent'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Basic Information
    reference_number = models.CharField(max_length=50, unique=True)
    subject = models.CharField(max_length=300)
    direction = models.CharField(max_length=10, choices=MEMO_DIRECTION)
    memo_type = models.ForeignKey(MemoType, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(MemoCategory, on_delete=models.SET_NULL, null=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Department Information
    sender_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='sent_memos')
    receiver_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='received_memos')
    
    # Registry Information
    registry_number = models.CharField(max_length=50, blank=True, help_text="Registry tracking number")
    dispatch_number = models.CharField(max_length=50, blank=True, help_text="Dispatch number for outgoing memos")
    received_from = models.CharField(max_length=200, blank=True, help_text="Person/Department who sent the memo")
    dispatched_to = models.CharField(max_length=200, blank=True, help_text="Person/Department the memo was dispatched to")
    
    # Date Information
    memo_date = models.DateField()
    received_date = models.DateField(null=True, blank=True)
    sent_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    dispatch_date = models.DateField(null=True, blank=True)
    response_date = models.DateField(null=True, blank=True)
    
    # Content
    content = models.TextField()
    summary = models.TextField(blank=True)
    attachments = models.FileField(upload_to='memos/%Y/%m/%d/', blank=True, null=True)
    
    # Response Tracking
    response_due_date = models.DateField(null=True, blank=True)
    response_content = models.TextField(blank=True, help_text="Content of the response memo")
    draft_response = models.FileField(upload_to='responses/draft/%Y/%m/%d/', blank=True, null=True)
    signed_response = models.FileField(upload_to='responses/signed/%Y/%m/%d/', blank=True, null=True)
    is_response_complete = models.BooleanField(default=False)
    
    # Status
    status = models.CharField(max_length=20, choices=MEMO_STATUS, default='draft')
    is_completed = models.BooleanField(default=False)
    requires_response = models.BooleanField(default=False)
    
    # Personnel Requirements
    requires_interpreter = models.BooleanField(default=False)
    requires_translator = models.BooleanField(default=False)
    number_of_interpreters = models.PositiveIntegerField(default=0)
    number_of_translators = models.PositiveIntegerField(default=0)
    language_requirements = models.TextField(blank=True, help_text="Languages required for interpreters/translators")
    
    # Document Uploads
    incoming_memo_file = models.FileField(
        upload_to='memos/incoming/%Y/%m/%d/', 
        blank=True, 
        null=True,
        help_text="Upload the original incoming memo (PDF, Word, Image)"
    )
    incoming_memo_scan = models.FileField(
        upload_to='memos/scans/%Y/%m/%d/', 
        blank=True, 
        null=True,
        help_text="Upload a scanned copy of the incoming memo"
    )
    outgoing_memo_file = models.FileField(
        upload_to='memos/outgoing/%Y/%m/%d/', 
        blank=True, 
        null=True,
        help_text="Upload the outgoing memo file"
    )
    supporting_documents = models.FileField(
        upload_to='memos/supporting/%Y/%m/%d/', 
        blank=True, 
        null=True,
        help_text="Upload any supporting documents"
    )
    
    # File metadata
    file_name = models.CharField(max_length=255, blank=True, help_text="Original file name")
    file_size = models.IntegerField(default=0, help_text="File size in bytes")
    file_type = models.CharField(max_length=100, blank=True, help_text="File MIME type")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_memos')
    upload_date = models.DateTimeField(null=True, blank=True)
    
    # Actions & Notes
    action_items = models.TextField(blank=True)
    action_taken = models.TextField(blank=True)
    remarks = models.TextField(blank=True)
    completion_notes = models.TextField(blank=True, help_text="Notes when the memo is completed")
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_memos')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_memos')
    last_updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_memos')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-memo_date', '-created_at']
        indexes = [
            models.Index(fields=['reference_number']),
            models.Index(fields=['direction']),
            models.Index(fields=['status']),
            models.Index(fields=['is_completed']),
            models.Index(fields=['registry_number']),
            models.Index(fields=['dispatch_number']),
        ]
    
    def __str__(self):
        return f"{self.reference_number} - {self.subject[:50]}"
    
    def save(self, *args, **kwargs):
        # Auto-generate reference number if not provided
        if not self.reference_number:
            prefix = 'IN' if self.direction == 'incoming' else 'OUT'
            year = timezone.now().strftime('%Y')
            count = Memo.objects.filter(direction=self.direction).count() + 1
            self.reference_number = f"{prefix}-{year}-{str(count).zfill(4)}"
        
        # Generate registry number for incoming memos
        if self.direction == 'incoming' and not self.registry_number:
            prefix = 'REG'
            year = timezone.now().strftime('%Y')
            count = Memo.objects.filter(direction='incoming').count() + 1
            self.registry_number = f"{prefix}-{year}-{str(count).zfill(4)}"
        
        # Generate dispatch number for outgoing memos
        if self.direction == 'outgoing' and not self.dispatch_number:
            prefix = 'DSP'
            year = timezone.now().strftime('%Y')
            count = Memo.objects.filter(direction='outgoing').count() + 1
            self.dispatch_number = f"{prefix}-{year}-{str(count).zfill(4)}"
        
        # Update completion status
        if self.status in ['completed', 'archived']:
            self.is_completed = True
            if not self.completed_date:
                self.completed_date = timezone.now().date()
        
        # Update response completion
        if self.requires_response and self.signed_response:
            self.is_response_complete = True
        
        # Update file metadata when uploading
        if self.incoming_memo_file and not self.file_name:
            self.file_name = self.incoming_memo_file.name
            self.file_size = self.incoming_memo_file.size
        
        super().save(*args, **kwargs)
    
    def mark_as_completed(self, notes=None):
        """Mark memo as completed"""
        self.status = 'completed'
        self.is_completed = True
        self.completed_date = timezone.now().date()
        if notes:
            self.completion_notes = notes
        self.save()
    
    def mark_response_sent(self):
        """Mark response as sent"""
        if self.requires_response:
            self.status = 'response_sent'
            self.response_date = timezone.now().date()
            self.is_response_complete = True
            self.save()
    
    def get_days_pending(self):
        """Calculate days memo has been pending"""
        if self.is_completed:
            return 0
        if self.due_date:
            days = (timezone.now().date() - self.due_date).days
            return max(0, days)
        return 0
    
    def is_overdue(self):
        """Check if memo is overdue"""
        if self.is_completed:
            return False
        if self.due_date:
            return timezone.now().date() > self.due_date
        return False
    
    def get_file_icon(self):
        """Get appropriate icon for file type"""
        if self.incoming_memo_file:
            ext = self.incoming_memo_file.name.split('.')[-1].lower()
            icons = {
                'pdf': 'fa-file-pdf',
                'doc': 'fa-file-word',
                'docx': 'fa-file-word',
                'xls': 'fa-file-excel',
                'xlsx': 'fa-file-excel',
                'jpg': 'fa-file-image',
                'jpeg': 'fa-file-image',
                'png': 'fa-file-image',
                'gif': 'fa-file-image',
                'txt': 'fa-file-alt',
                'zip': 'fa-file-archive',
                'rar': 'fa-file-archive',
            }
            return icons.get(ext, 'fa-file')
        return 'fa-file'
    
    def get_workflow_steps(self):
        """Get workflow steps for the memo"""
        steps = []
        if self.direction == 'incoming':
            steps = [
                {'status': 'registered', 'label': 'Registered', 'icon': 'fa-check-circle', 'completed': True},
                {'status': 'dispatched', 'label': 'Dispatched to OIC/HoD', 'icon': 'fa-paper-plane', 
                 'completed': self.status in ['dispatched', 'in_progress', 'response_required', 'response_prepared', 'response_sent', 'completed']},
                {'status': 'in_progress', 'label': 'In Progress/Review', 'icon': 'fa-spinner',
                 'completed': self.status in ['in_progress', 'response_required', 'response_prepared', 'response_sent', 'completed']},
                {'status': 'response_required', 'label': 'Response Required', 'icon': 'fa-reply',
                 'completed': self.status in ['response_prepared', 'response_sent', 'completed']},
                {'status': 'response_prepared', 'label': 'Draft Response Ready', 'icon': 'fa-file-alt',
                 'completed': self.status in ['response_prepared', 'response_sent', 'completed']},
                {'status': 'response_sent', 'label': 'Response Sent', 'icon': 'fa-check-double',
                 'completed': self.status in ['response_sent', 'completed']},
                {'status': 'completed', 'label': 'Completed', 'icon': 'fa-check-circle',
                 'completed': self.status == 'completed'},
            ]
        else:
            steps = [
                {'status': 'draft', 'label': 'Draft Created', 'icon': 'fa-pencil', 'completed': True},
                {'status': 'sent', 'label': 'Sent to Registry', 'icon': 'fa-send',
                 'completed': self.status in ['sent', 'received', 'in_progress', 'completed']},
                {'status': 'received', 'label': 'Received by Recipient', 'icon': 'fa-inbox',
                 'completed': self.status in ['received', 'in_progress', 'completed']},
                {'status': 'in_progress', 'label': 'In Progress', 'icon': 'fa-spinner',
                 'completed': self.status in ['in_progress', 'completed']},
                {'status': 'completed', 'label': 'Completed', 'icon': 'fa-check-circle',
                 'completed': self.status == 'completed'},
            ]
        return steps

class MemoAction(models.Model):
    """Actions taken on memos"""
    ACTION_TYPES = [
        ('created', 'Created'),
        ('registered', 'Registered'),
        ('dispatched', 'Dispatched'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('response_drafted', 'Response Drafted'),
        ('response_signed', 'Response Signed'),
        ('response_sent', 'Response Sent'),
        ('comment', 'Comment Added'),
        ('attachment_added', 'Attachment Added'),
        ('status_changed', 'Status Changed'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived'),
    ]
    
    memo = models.ForeignKey(Memo, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    description = models.TextField()
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    performed_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-performed_at']
    
    def __str__(self):
        return f"{self.get_action_type_display()} - {self.memo.reference_number}"

class MemoAssignment(models.Model):
    """Assignment of personnel to memo requests"""
    memo = models.ForeignKey(Memo, on_delete=models.CASCADE, related_name='assignments')
    personnel = models.ForeignKey('personnel.Personnel', on_delete=models.CASCADE, related_name='memo_assignments')
    assignment_type = models.CharField(max_length=20, choices=[
        ('interpreter', 'Interpreter'),
        ('translator', 'Translator'),
    ])
    assigned_at = models.DateTimeField(auto_now_add=True)
    confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-assigned_at']
        unique_together = ['memo', 'personnel', 'assignment_type']
    
    def __str__(self):
        return f"{self.memo.reference_number} - {self.personnel.full_name()}"

class MemoComment(models.Model):
    """Comments on memos"""
    memo = models.ForeignKey(Memo, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment on {self.memo.reference_number}"