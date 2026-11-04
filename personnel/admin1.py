from django.utils.safestring import mark_safe   # add at top

# Register your models here.
# personnel/admin.py

from django.contrib import admin
from django.utils.html import format_html, format_html_join
from django.urls import reverse
from django.utils import timezone
from .models import (
    Meeting, Personnel, Document, Payment, 
    CommunicationLog, NotificationTemplate, UploadHistory
)

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'start_date', 'end_date', 'status', 'days_duration']
    list_filter = ['status', 'start_date']
    search_fields = ['name', 'location']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']

@admin.register(Personnel)
class PersonnelAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'personnel_type', 'nationality', 'email', 
        'city_departure', 'documents_complete', 'document_status_display', 'is_active'
    ]
    list_filter = ['personnel_type', 'nationality', 'documents_complete', 'is_active']
    search_fields = ['first_name', 'last_name', 'email', 'nationality']
    list_editable = ['documents_complete', 'is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'middle_name', 'last_name', 'gender', 'date_of_birth', 
                      'nationality', 'email', 'phone', 'alternative_phone')
        }),
        ('Professional Information', {
            'fields': ('personnel_type', 'designation', 'languages', 'city_departure')
        }),
        ('Assignment', {
            'fields': ('meeting', 'is_active', 'documents_complete')
        }),
        ('Additional Information', {
            'fields': ('notes', 'emergency_contact_name', 'emergency_contact_phone'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def document_status_display(self, obj):
        doc_status = obj.get_document_status()
        icons = format_html_join(
            '',
            '<span class="badge {}" title="{}">{}</span>',
            (
                ('bg-success' if info['uploaded'] else 'bg-danger',
                info['file_name'] or doc_type,      # ← auto-escaped by format_html
                doc_type.replace('_', ' ').title())
                for doc_type, info in doc_status.items()
            ),
        )
        return format_html('<div class="docs">{}</div>', icons)
    # def document_status_display(self, obj):
    #     """Display document status with icons"""
    #     status = obj.get_document_status()
    #     html = '<div style="display: flex; gap: 5px; flex-wrap: wrap;">'
    #     for doc_type, info in status.items():
    #         icon = '✅' if info['uploaded'] else '❌'
    #         color = 'green' if info['uploaded'] else 'red'
    #         html += f'<span style="color: {color};" title="{doc_type}"> {icon} </span>'
    #     html += '</div>'
    #     return mark_safe(html)   # ← use mark_safe instead of format_html
    document_status_display.short_description = 'Documents'
    
    def view_documents_link(self, obj):
        url = reverse('admin:personnel_document_changelist') + f'?personnel__id__exact={obj.id}'
        return format_html(f'<a href="{url}">View Documents</a>')
    view_documents_link.short_description = 'Documents'

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'personnel', 'document_type_display', 'file_name', 
        'is_complete', 'is_verified', 'upload_date', 'file_size_display'
    ]
    list_filter = ['document_type', 'is_complete', 'is_verified', 'upload_date']
    search_fields = ['personnel__first_name', 'personnel__last_name', 'file_name']
    readonly_fields = ['upload_date', 'file_size', 'mime_type']
    
    actions = ['verify_documents', 'mark_as_incomplete']
    
    def document_type_display(self, obj):
        return obj.get_document_type_display()
    document_type_display.short_description = 'Document Type'
    
    def file_size_display(self, obj):
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.2f} KB"
        else:
            return f"{obj.file_size / (1024 * 1024):.2f} MB"
    file_size_display.short_description = 'File Size'
    
    def verify_documents(self, request, queryset):
        queryset.update(is_verified=True, verification_date=timezone.now())
        self.message_user(request, f"{queryset.count()} documents verified successfully.")
    verify_documents.short_description = "Verify selected documents"
    
    def mark_as_incomplete(self, request, queryset):
        queryset.update(is_complete=False)
        self.message_user(request, f"{queryset.count()} documents marked as incomplete.")

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'personnel', 'total_amount', 'currency', 'payment_status', 
        'finance_submission_date', 'payment_date'
    ]
    list_filter = ['payment_status', 'currency', 'role_type']
    search_fields = ['personnel__first_name', 'personnel__last_name', 'payment_reference']
    readonly_fields = ['created_at', 'updated_at', 'subtotal', 'tax']
    
    actions = ['approve_payments', 'mark_as_paid', 'send_to_finance']
    
    def approve_payments(self, request, queryset):
        queryset.update(payment_status='approved')
        self.message_user(request, f"{queryset.count()} payments approved.")
    approve_payments.short_description = "Approve selected payments"
    
    def mark_as_paid(self, request, queryset):
        queryset.update(payment_status='paid', payment_date=timezone.now())
        self.message_user(request, f"{queryset.count()} payments marked as paid.")
    mark_as_paid.short_description = "Mark selected as paid"
    
    def send_to_finance(self, request, queryset):
        queryset.update(payment_status='submitted_to_finance', finance_submission_date=timezone.now())
        self.message_user(request, f"{queryset.count()} payments sent to finance.")
    send_to_finance.short_description = "Send selected to finance"

@admin.register(CommunicationLog)
class CommunicationLogAdmin(admin.ModelAdmin):
    list_display = ['personnel', 'communication_type', 'subject', 'status', 'sent_date']
    list_filter = ['communication_type', 'status', 'sent_date']
    search_fields = ['personnel__first_name', 'personnel__last_name', 'subject']
    readonly_fields = ['sent_date']

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'is_active', 'updated_at']
    list_filter = ['template_type', 'is_active']
    search_fields = ['name', 'subject_template']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'template_type', 'is_active')
        }),
        ('Content', {
            'fields': ('subject_template', 'body_template', 'html_template')
        }),
    )

@admin.register(UploadHistory)
class UploadHistoryAdmin(admin.ModelAdmin):
    list_display = ['personnel', 'document', 'uploaded_by', 'upload_date']
    list_filter = ['upload_date']
    search_fields = ['personnel__first_name', 'personnel__last_name']
    readonly_fields = ['upload_date', 'ip_address', 'user_agent']

# personnel/admin.py

from django.contrib import admin
from django import forms
from django.urls import reverse
from django.utils.html import format_html
from .models import PaymentSetting, Personnel, Document, Payment, Meeting

@admin.register(PaymentSetting)
class PaymentSettingAdmin(admin.ModelAdmin):
    list_display = ['rate_type_display', 'value', 'is_active', 'updated_at']
    list_filter = ['is_active', 'rate_type']
    search_fields = ['rate_type', 'description']
    list_editable = ['value', 'is_active']
    fields = ['rate_type', 'value', 'description', 'is_active']
    readonly_fields = ['rate_type_display']
    
    def rate_type_display(self, obj):
        return obj.get_rate_type_display()
    rate_type_display.short_description = 'Rate Type'
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'rate_type' in form.base_fields:
            form.base_fields['rate_type'].widget = forms.Select(choices=PaymentSetting.RATE_TYPES)
        return form
    
    def save_model(self, request, obj, form, change):
        if obj.pk:  # Existing object
            obj.updated_by = request.user
        else:  # New object
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)