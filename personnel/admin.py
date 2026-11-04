# personnel/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    Meeting,
    Personnel,
    Document,
    Payment,
    CommunicationLog,
    NotificationTemplate,
    UploadHistory,
    PaymentSetting,
    DocumentMerge,
    MergedDocument,
    MeetingAssignment,
)


# ---------- MEETING ----------
@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'start_date', 'end_date', 'status', 'personnel_count')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('name', 'location', 'description')
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)

    @admin.display(description='Personnel')
    def personnel_count(self, obj):
        return obj.personnel.count()


# ---------- PERSONNEL ----------
@admin.register(Personnel)
class PersonnelAdmin(admin.ModelAdmin):
    list_display = (
        'full_name_display',
        'personnel_type',
        'sub_type',
        'nationality',
        'email',
        'meeting',
        'documents_complete',
        'is_active',
    )
    list_filter = (
        'personnel_type',
        'translator_type',
        'interpreter_type',
        'documents_complete',
        'is_active',
        'meeting',
    )
    search_fields = (
        'first_name',
        'last_name',
        'middle_name',
        'email',
        'phone',
        'nationality',
    )
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('created_by',)
    date_hierarchy = 'created_at'
    ordering = ('last_name', 'first_name')

    fieldsets = (
        ('Personal', {
            'fields': (
                'first_name', 'middle_name', 'last_name',
                'gender', 'date_of_birth', 'nationality',
                'photo',
            )
        }),
        ('Contact', {
            'fields': ('email', 'phone', 'alternative_phone')
        }),
        ('Professional', {
            'fields': (
                'personnel_type', 'translator_type', 'interpreter_type',
                'designation', 'languages', 'city_departure',
            )
        }),
        ('Assignment', {
            'fields': ('meeting', 'is_active', 'documents_complete')
        }),
        ('Emergency', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone'),
            'classes': ('collapse',),
        }),
        ('Notes & Meta', {
            'fields': ('notes', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Name')
    def full_name_display(self, obj):
        return obj.full_name()

    @admin.display(description='Sub-type')
    def sub_type(self, obj):
        if obj.personnel_type == 'translator':
            return obj.translator_type or '—'
        if obj.personnel_type == 'interpreter':
            return obj.interpreter_type or '—'
        return '—'


# ---------- DOCUMENT ----------
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        'personnel_name', 'document_type', 'file_name',
        'is_complete', 'is_verified', 'upload_date',
    )
    list_filter = ('document_type', 'is_complete', 'is_verified', 'upload_date')
    search_fields = (
        'personnel__first_name',
        'personnel__last_name',
        'file_name',
    )
    raw_id_fields = ('personnel', 'verified_by')
    readonly_fields = ('upload_date', 'file_name', 'file_size', 'mime_type')
    date_hierarchy = 'upload_date'

    @admin.display(description='Personnel')
    def personnel_name(self, obj):
        return obj.personnel.full_name()


# ---------- PAYMENT ----------
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'personnel_name', 'role_type', 'total_amount',
        'currency', 'payment_status', 'created_at',
    )
    list_filter = ('payment_status', 'currency', 'role_type')
    search_fields = ('personnel__first_name', 'personnel__last_name')
    raw_id_fields = ('personnel', 'meeting', 'processed_by')
    readonly_fields = ('created_at', 'updated_at', 'subtotal', 'tax', 'total_amount')
    date_hierarchy = 'created_at'

    @admin.display(description='Personnel')
    def personnel_name(self, obj):
        return obj.personnel.full_name()


# ---------- COMMUNICATION LOG ----------
@admin.register(CommunicationLog)
class CommunicationLogAdmin(admin.ModelAdmin):
    list_display = ('sent_date', 'personnel_name', 'communication_type', 'subject', 'status')
    list_filter = ('status', 'communication_type', 'sent_date')
    search_fields = ('subject', 'recipient_email', 'personnel__first_name', 'personnel__last_name')
    readonly_fields = ('sent_date',)
    raw_id_fields = ('personnel',)
    date_hierarchy = 'sent_date'

    @admin.display(description='Personnel')
    def personnel_name(self, obj):
        return obj.personnel.full_name() if obj.personnel else '—'


# ---------- NOTIFICATION TEMPLATE ----------
@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_type', 'is_active', 'updated_at')
    list_filter = ('template_type', 'is_active')
    search_fields = ('name', 'subject_template')


# ---------- UPLOAD HISTORY ----------
@admin.register(UploadHistory)
class UploadHistoryAdmin(admin.ModelAdmin):
    list_display = ('upload_date', 'personnel_name', 'document_type', 'uploaded_by')
    list_filter = ('upload_date',)
    search_fields = ('personnel__first_name', 'personnel__last_name')
    raw_id_fields = ('personnel', 'document', 'uploaded_by')
    readonly_fields = ('upload_date',)
    date_hierarchy = 'upload_date'

    @admin.display(description='Personnel')
    def personnel_name(self, obj):
        return obj.personnel.full_name()

    @admin.display(description='Document')
    def document_type(self, obj):
        return obj.document.get_document_type_display()


# ---------- PAYMENT SETTING ----------
@admin.register(PaymentSetting)
class PaymentSettingAdmin(admin.ModelAdmin):
    list_display = ('rate_type', 'value', 'is_active', 'updated_at')
    list_filter = ('is_active', 'rate_type')
    search_fields = ('rate_type',)
    readonly_fields = ('updated_at',)
    raw_id_fields = ('updated_by',)


# ---------- DOCUMENT MERGE ----------
@admin.register(DocumentMerge)
class DocumentMergeAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'personnel_name', 'format', 'status', 'file_size', 'total_documents')
    list_filter = ('format', 'status')
    search_fields = ('personnel__first_name', 'personnel__last_name')
    raw_id_fields = ('personnel', 'created_by')
    readonly_fields = ('created_at', 'completed_at')
    date_hierarchy = 'created_at'

    @admin.display(description='Personnel')
    def personnel_name(self, obj):
        return obj.personnel.full_name()


# ---------- MERGED DOCUMENT ----------
@admin.register(MergedDocument)
class MergedDocumentAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'personnel_name', 'file_size', 'total_documents')
    search_fields = ('personnel__first_name', 'personnel__last_name')
    raw_id_fields = ('personnel', 'created_by')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

    @admin.display(description='Personnel')
    def personnel_name(self, obj):
        return obj.personnel.full_name()


# ---------- MEETING ASSIGNMENT ----------
@admin.register(MeetingAssignment)
class MeetingAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        'username_for_meeting',
        'personnel_name',
        'meeting_name',
        'role',
        'is_active',
        'credentials_sent_at',
        'created_at',
    )
    list_filter = ('role', 'is_active', 'meeting')
    search_fields = (
        'username_for_meeting',
        'user__username',
        'user__email',
        'personnel__first_name',
        'personnel__last_name',
        'personnel__email',
        'meeting__name',
    )
    readonly_fields = (
        'user',
        'personnel',
        'meeting',
        'role',
        'username_for_meeting',
        'plain_password_hint',
        'created_at',
        'credentials_sent_at',
    )
    raw_id_fields = ('user', 'personnel', 'meeting')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    fieldsets = (
        ('Assignment', {
            'fields': ('user', 'personnel', 'meeting', 'role', 'username_for_meeting')
        }),
        ('Status', {
            'fields': ('is_active', 'credentials_sent_at', 'created_at')
        }),
        ('Security', {
            'fields': ('plain_password_hint',),
            'classes': ('collapse',),
            'description': 'Cleared automatically after the credentials email is sent.',
        }),
    )

    @admin.display(description='Personnel')
    def personnel_name(self, obj):
        return obj.personnel.full_name()

    @admin.display(description='Meeting')
    def meeting_name(self, obj):
        return obj.meeting.name

    def has_add_permission(self, request):
        return False
    
# personnel/admin.py — append

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'name', 'email', 'subject', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('name', 'email', 'phone', 'subject', 'message',
                       'ip_address', 'user_agent', 'created_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    fieldsets = (
        ('Sender', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Message', {
            'fields': ('subject', 'message', 'created_at', 'ip_address', 'user_agent')
        }),
        ('Handling', {
            'fields': ('status', 'admin_notes', 'replied_at', 'replied_by')
        }),
    )

    actions = ['mark_read', 'mark_replied', 'mark_archived']

    @admin.action(description='Mark selected as Read')
    def mark_read(self, request, queryset):
        n = queryset.update(status='read')
        self.message_user(request, f"{n} message(s) marked as read.")

    @admin.action(description='Mark selected as Replied')
    def mark_replied(self, request, queryset):
        from django.utils import timezone
        n = queryset.update(status='replied', replied_at=timezone.now(), replied_by=request.user)
        self.message_user(request, f"{n} message(s) marked as replied.")

    @admin.action(description='Archive selected')
    def mark_archived(self, request, queryset):
        n = queryset.update(status='archived')
        self.message_user(request, f"{n} message(s) archived.")

from .models import PersonnelMaster

@admin.register(PersonnelMaster)
class PersonnelMasterAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'middle_name', 'last_name', 'gender', 'nationality', 'email', 'phone', 'is_active')
    list_filter = ('nationality', 'gender', 'is_active')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    ordering = ('first_name', 'last_name')
    list_editable = ('is_active',)
    fieldsets = (
        ('Name', {
            'fields': ('first_name', 'middle_name', 'last_name')
        }),
        ('Personal', {
            'fields': ('gender', 'date_of_birth', 'nationality')
        }),
        ('Contact', {
            'fields': ('email', 'phone', 'alternate_phone')
        }),
        ('Other', {
            'fields': ('city_departure', 'is_active')
        }),
    )