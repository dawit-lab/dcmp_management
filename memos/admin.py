from django.contrib import admin
from .models import Department, MemoType, MemoCategory, Memo, MemoAction, MemoComment

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active']
    search_fields = ['name', 'code']
    list_filter = ['is_active']
    ordering = ['name']

@admin.register(MemoType)
class MemoTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name', 'code']
    ordering = ['name']

@admin.register(MemoCategory)
class MemoCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type']
    search_fields = ['name']
    list_filter = ['category_type']
    ordering = ['name']

@admin.register(Memo)
class MemoAdmin(admin.ModelAdmin):
    list_display = ['reference_number', 'subject', 'direction', 'status', 'priority', 'created_at']
    search_fields = ['reference_number', 'subject', 'content']
    list_filter = ['direction', 'status', 'priority', 'created_at']
    date_hierarchy = 'created_at'
    readonly_fields = ['reference_number', 'registry_number', 'dispatch_number']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('direction', 'reference_number', 'subject', 'memo_type', 'category', 'priority')
        }),
        ('Departments', {
            'fields': ('sender_department', 'receiver_department')
        }),
        ('Registry Information', {
            'fields': ('registry_number', 'dispatch_number', 'received_from', 'dispatched_to')
        }),
        ('Dates', {
            'fields': ('memo_date', 'received_date', 'sent_date', 'due_date', 'completed_date')
        }),
        ('Content', {
            'fields': ('content', 'summary')
        }),
        ('Personnel Requirements', {
            'fields': ('requires_interpreter', 'requires_translator', 
                      'number_of_interpreters', 'number_of_translators', 'language_requirements')
        }),
        ('Status & Tracking', {
            'fields': ('status', 'is_completed', 'requires_response', 'is_response_complete')
        }),
        ('Actions', {
            'fields': ('action_items', 'action_taken', 'remarks', 'completion_notes')
        }),
        ('Users', {
            'fields': ('created_by', 'assigned_to', 'last_updated_by')
        }),
    )