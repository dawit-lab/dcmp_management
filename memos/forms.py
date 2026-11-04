# memos/forms.py - Complete corrected MemoForm

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Memo, Department, MemoType, MemoCategory, MemoComment

class MemoForm(forms.ModelForm):
    """Main memo form with all fields"""
    
    class Meta:
        model = Memo
        fields = [
            'direction', 'subject', 'memo_type', 'category', 'priority',
            'sender_department', 'receiver_department', 'memo_date',
            'received_date', 'sent_date', 'due_date', 'content',
            'summary', 'requires_interpreter', 'requires_translator',
            'number_of_interpreters', 'number_of_translators',
            'language_requirements', 'action_items', 'remarks',
            'assigned_to', 'status', 'requires_response', 'response_due_date',
            'received_from', 'dispatched_to', 'registry_number', 'dispatch_number',
            'incoming_memo_file', 'incoming_memo_scan', 'outgoing_memo_file', 
            'supporting_documents'
        ]
        widgets = {
            'memo_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'received_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'sent_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'response_due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'content': forms.Textarea(attrs={'rows': 8, 'class': 'form-control'}),
            'summary': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'action_items': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'action_taken': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'language_requirements': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'incoming_memo_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'}),
            'incoming_memo_scan': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
            'outgoing_memo_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'supporting_documents': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            elif isinstance(field.widget, forms.Textarea):
                pass  # Already handled in widgets
            elif isinstance(field.widget, forms.DateInput):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif not isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control'})
        
        # ============================================================
        # Add "Add New" option to dropdown fields
        # ============================================================
        
        # Memo Type
        if 'memo_type' in self.fields:
            current_choices = list(self.fields['memo_type'].choices)
            if not any(choice[0] == '__new__' for choice in current_choices):
                self.fields['memo_type'].choices = current_choices + [('__new__', '➕ Add New Memo Type')]
            self.fields['memo_type'].widget.attrs.update({
                'data-add-url': '/memos/api/create-memo-type/',
                'data-add-field': 'memo_type'
            })
        
        # Category
        if 'category' in self.fields:
            current_choices = list(self.fields['category'].choices)
            if not any(choice[0] == '__new__' for choice in current_choices):
                self.fields['category'].choices = current_choices + [('__new__', '➕ Add New Category')]
            self.fields['category'].widget.attrs.update({
                'data-add-url': '/memos/api/create-category/',
                'data-add-field': 'category'
            })
        
        # Sender Department - Use the same department queryset
        if 'sender_department' in self.fields:
            current_choices = list(self.fields['sender_department'].choices)
            if not any(choice[0] == '__new__' for choice in current_choices):
                self.fields['sender_department'].choices = current_choices + [('__new__', '➕ Add New Department')]
            self.fields['sender_department'].widget.attrs.update({
                'data-add-url': '/memos/api/create-department/',
                'data-add-field': 'sender_department'
            })
        
        # Receiver Department - Use the same department queryset
        if 'receiver_department' in self.fields:
            current_choices = list(self.fields['receiver_department'].choices)
            if not any(choice[0] == '__new__' for choice in current_choices):
                self.fields['receiver_department'].choices = current_choices + [('__new__', '➕ Add New Department')]
            self.fields['receiver_department'].widget.attrs.update({
                'data-add-url': '/memos/api/create-department/',
                'data-add-field': 'receiver_department'
            })
        
        # Set initial values for new memos
        if not self.instance.pk:
            self.fields['memo_date'].initial = timezone.now().date()
        
        # Hide auto-generated fields
        if not self.instance.pk:
            self.fields['registry_number'].widget = forms.HiddenInput()
            self.fields['dispatch_number'].widget = forms.HiddenInput()
    
    def clean_incoming_memo_file(self):
        """Validate incoming memo file"""
        file = self.cleaned_data.get('incoming_memo_file')
        if file:
            if file.size > 10 * 1024 * 1024:
                raise ValidationError("File size cannot exceed 10MB.")
            
            allowed_extensions = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'tiff', 'bmp']
            ext = file.name.split('.')[-1].lower()
            if ext not in allowed_extensions:
                raise ValidationError(f"File type not allowed. Allowed: {', '.join(allowed_extensions)}")
        return file
    
    def clean(self):
        cleaned_data = super().clean()
        direction = cleaned_data.get('direction')
        
        # Validation for incoming memos
        if direction == 'incoming':
            if not cleaned_data.get('sender_department'):
                raise ValidationError("Sender department is required for incoming memos")
            if not cleaned_data.get('received_date'):
                cleaned_data['received_date'] = timezone.now().date()
            
            if not cleaned_data.get('incoming_memo_file') and not self.instance.pk:
                raise ValidationError("Please upload the incoming memo file")
        
        # Validation for outgoing memos
        if direction == 'outgoing':
            if not cleaned_data.get('receiver_department'):
                raise ValidationError("Receiver department is required for outgoing memos")
            if not cleaned_data.get('sent_date'):
                cleaned_data['sent_date'] = timezone.now().date()
            
            if not cleaned_data.get('outgoing_memo_file') and not self.instance.pk:
                raise ValidationError("Please upload the outgoing memo file")
        
        # Validate interpreter/translator requirements
        if cleaned_data.get('requires_interpreter') and not cleaned_data.get('number_of_interpreters'):
            raise ValidationError("Please specify the number of interpreters required")
        
        if cleaned_data.get('requires_translator') and not cleaned_data.get('number_of_translators'):
            raise ValidationError("Please specify the number of translators required")
        
        if cleaned_data.get('requires_response') and not cleaned_data.get('response_due_date'):
            raise ValidationError("Please specify a response due date")
        
        return cleaned_data


class MemoUploadForm(forms.ModelForm):
    """Simplified form for uploading incoming memos"""
    
    class Meta:
        model = Memo
        fields = [
            'direction', 'subject', 'sender_department', 'receiver_department',
            'memo_date', 'received_date', 'incoming_memo_file', 'incoming_memo_scan',
            'supporting_documents', 'priority', 'category', 'remarks'
        ]
        widgets = {
            'memo_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'received_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'incoming_memo_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'}),
            'incoming_memo_scan': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
            'supporting_documents': forms.FileInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'sender_department': forms.Select(attrs={'class': 'form-select'}),
            'receiver_department': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'remarks': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['direction'].initial = 'incoming'
        self.fields['direction'].widget = forms.HiddenInput()
        self.fields['received_date'].initial = timezone.now().date()
    
    def clean_incoming_memo_file(self):
        file = self.cleaned_data.get('incoming_memo_file')
        if not file:
            raise ValidationError("Please upload the incoming memo file")
        if file.size > 10 * 1024 * 1024:
            raise ValidationError("File size cannot exceed 10MB.")
        return file


class MemoCommentForm(forms.ModelForm):
    class Meta:
        model = MemoComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add your comment...'
            })
        }


class ResponseForm(forms.ModelForm):
    """Form for uploading response documents"""
    class Meta:
        model = Memo
        fields = ['draft_response', 'signed_response', 'response_content']
        widgets = {
            'response_content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Enter response content...'
            }),
            'draft_response': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'signed_response': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
        }