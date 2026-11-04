# personnel/forms.py

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from .models import Personnel, Document, Payment, Meeting, UploadHistory


# ---------- MEETING LOCATION (Country + Capital) ----------
AFRICAN_COUNTRY_CAPITALS = [
    ('Algeria - Algiers', 'Algeria - Algiers'),
    ('Angola - Luanda', 'Angola - Luanda'),
    ('Benin - Porto-Novo', 'Benin - Porto-Novo'),
    ('Botswana - Gaborone', 'Botswana - Gaborone'),
    ('Burkina Faso - Ouagadougou', 'Burkina Faso - Ouagadougou'),
    ('Burundi - Bujumbra', 'Burundi - Bujumbra'),
    ('Cabo Verde - Praia', 'Cabo Verde - Praia'),
    ('Cameroon - Yaoundé', 'Cameroon - Yaoundé'),
    ('Central African Republic - Bangui', 'Central African Republic - Bangui'),
    ('Chad - N\'Djamena', 'Chad - N\'Djamena'),
    ('Comoros - Moroni', 'Comoros - Moroni'),
    ('Congo - Brazzaville', 'Congo - Brazzaville'),
    ('Congo (DRC) - Kinshasa', 'Congo (DRC) - Kinshasa'),
    ('Djibouti - Djibouti', 'Djibouti - Djibouti'),
    ('Egypt - Cairo', 'Egypt - Cairo'),
    ('Equatorial Guinea - Malabo', 'Equatorial Guinea - Malabo'),
    ('Eritrea - Asmara', 'Eritrea - Asmara'),
    ('Eswatini - Mbabane', 'Eswatini - Mbabane'),
    ('Ethiopia - Addis Ababa', 'Ethiopia - Addis Ababa'),
    ('Gabon - Libreville', 'Gabon - Libreville'),
    ('Gambia - Banjul', 'Gambia - Banjul'),
    ('Ghana - Accra', 'Ghana - Accra'),
    ('Guinea - Conakry', 'Guinea - Conakry'),
    ('Guinea-Bissau - Bissau', 'Guinea-Bissau - Bissau'),
    ('Ivory Coast - Yamoussoukro', 'Ivory Coast - Yamoussoukro'),
    ('Kenya - Nairobi', 'Kenya - Nairobi'),
    ('Lesotho - Maseru', 'Lesotho - Maseru'),
    ('Liberia - Monrovia', 'Liberia - Monrovia'),
    ('Libya - Tripoli', 'Libya - Tripoli'),
    ('Madagascar - Antananarivo', 'Madagascar - Antananarivo'),
    ('Malawi - Lilongwe', 'Malawi - Lilongwe'),
    ('Mali - Bamako', 'Mali - Bamako'),
    ('Mauritania - Nouakchott', 'Mauritania - Nouakchott'),
    ('Mauritius - Port Louis', 'Mauritius - Port Louis'),
    ('Morocco - Rabat', 'Morocco - Rabat'),
    ('Mozambique - Maputo', 'Mozambique - Maputo'),
    ('Namibia - Windhoek', 'Namibia - Windhoek'),
    ('Niger - Niamey', 'Niger - Niamey'),
    ('Nigeria - Abuja', 'Nigeria - Abuja'),
    ('Rwanda - Kigali', 'Rwanda - Kigali'),
    ('Sao Tome and Principe - São Tomé', 'Sao Tome and Principe - São Tomé'),
    ('Senegal - Dakar', 'Senegal - Dakar'),
    ('Seychelles - Victoria', 'Seychelles - Victoria'),
    ('Sierra Leone - Freetown', 'Sierra Leone - Freetown'),
    ('Somalia - Mogadishu', 'Somalia - Mogadishu'),
    ('South Africa - Pretoria', 'South Africa - Pretoria'),
    ('South Sudan - Juba', 'South Sudan - Juba'),
    ('Sudan - Khartoum', 'Sudan - Khartoum'),
    ('Tanzania - Dodoma', 'Tanzania - Dodoma'),
    ('Togo - Lomé', 'Togo - Lomé'),
    ('Tunisia - Tunis', 'Tunisia - Tunis'),
    ('Uganda - Kampala', 'Uganda - Kampala'),
    ('Zambia - Lusaka', 'Zambia - Lusaka'),
    ('Zimbabwe - Harare', 'Zimbabwe - Harare'),
]

# ---------- PERSONNEL NATIONALITY (Country only) ----------
AFRICAN_COUNTRIES = [
    ('Algeria', 'Algeria'),
    ('Angola', 'Angola'),
    ('Benin', 'Benin'),
    ('Botswana', 'Botswana'),
    ('Burkina Faso', 'Burkina Faso'),
    ('Burundi', 'Burundi'),
    ('Cabo Verde', 'Cabo Verde'),
    ('Cameroon', 'Cameroon'),
    ('Central African Republic', 'Central African Republic'),
    ('Chad', 'Chad'),
    ('Comoros', 'Comoros'),
    ('Congo', 'Congo'),
    ('Congo (DRC)', 'Congo (DRC)'),
    ('Djibouti', 'Djibouti'),
    ('Egypt', 'Egypt'),
    ('Equatorial Guinea', 'Equatorial Guinea'),
    ('Eritrea', 'Eritrea'),
    ('Eswatini', 'Eswatini'),
    ('Ethiopia', 'Ethiopia'),
    ('Gabon', 'Gabon'),
    ('Gambia', 'Gambia'),
    ('Ghana', 'Ghana'),
    ('Guinea', 'Guinea'),
    ('Guinea-Bissau', 'Guinea-Bissau'),
    ('Ivory Coast', 'Ivory Coast'),
    ('Kenya', 'Kenya'),
    ('Lesotho', 'Lesotho'),
    ('Liberia', 'Liberia'),
    ('Libya', 'Libya'),
    ('Madagascar', 'Madagascar'),
    ('Malawi', 'Malawi'),
    ('Mali', 'Mali'),
    ('Mauritania', 'Mauritania'),
    ('Mauritius', 'Mauritius'),
    ('Morocco', 'Morocco'),
    ('Mozambique', 'Mozambique'),
    ('Namibia', 'Namibia'),
    ('Niger', 'Niger'),
    ('Nigeria', 'Nigeria'),
    ('Rwanda', 'Rwanda'),
    ('Sao Tome and Principe', 'Sao Tome and Principe'),
    ('Senegal', 'Senegal'),
    ('Seychelles', 'Seychelles'),
    ('Sierra Leone', 'Sierra Leone'),
    ('Somalia', 'Somalia'),
    ('South Africa', 'South Africa'),
    ('South Sudan', 'South Sudan'),
    ('Sudan', 'Sudan'),
    ('Tanzania', 'Tanzania'),
    ('Togo', 'Togo'),
    ('Tunisia', 'Tunisia'),
    ('Uganda', 'Uganda'),
    ('Zambia', 'Zambia'),
    ('Zimbabwe', 'Zimbabwe'),
]


# ---------- PERSONNEL FORM ----------
class PersonnelForm(forms.ModelForm):
    """Form for creating and editing personnel"""
    
    nationality = forms.ChoiceField(
        choices=AFRICAN_COUNTRIES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        label='Nationality'
    )

    LANGUAGES = [
        ('arabic', 'Arabic'),
        ('english', 'English'),
        ('french', 'French'),
        ('portuguese', 'Portuguese'),
        ('spanish', 'Spanish'),
        ('kiswahili', 'Kiswahili'),
    ]
    
    languages = forms.MultipleChoiceField(
        choices=LANGUAGES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        help_text="Select the languages spoken"
    )

    translator_type = forms.ChoiceField(
        choices=Personnel.TRANSLATOR_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        label='Translator Type'
    )
    
    interpreter_type = forms.ChoiceField(
        choices=Personnel.INTERPRETER_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        label='Interpreter Type'
    )
    
    # Photo field
    photo = forms.ImageField(
        required=False,
        label='Passport Photo',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text='Upload a passport-style photo (JPG, PNG, GIF - max 5MB)'
    )
    
    class Meta:
        model = Personnel
        fields = [
            'first_name', 'middle_name', 'last_name', 'gender', 'date_of_birth',
            'nationality', 'email', 'phone', 'alternative_phone',
            'personnel_type', 'translator_type', 'interpreter_type', 'designation', 
            'languages', 'city_departure',
            'meeting', 'notes', 'emergency_contact_name', 'emergency_contact_phone',
            'photo'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'nationality': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'alternative_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'city_departure': forms.TextInput(attrs={'class': 'form-control'}),
            'personnel_type': forms.Select(attrs={'class': 'form-select'}),
            'translator_type': forms.Select(attrs={'class': 'form-select'}),
            'interpreter_type': forms.Select(attrs={'class': 'form-select'}),
            'designation': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'meeting': forms.Select(attrs={'class': 'form-select form-select-lg flex-grow-1'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If editing and the stored nationality isn't in the dropdown, add it
        if self.instance and self.instance.pk and self.instance.nationality:
            current = self.instance.nationality
            values = [choice[0] for choice in self.fields['nationality'].choices]
            if current not in values:
                self.fields['nationality'].choices = list(self.fields['nationality'].choices) + [(current, current)]

        # Set initial languages
        if self.instance and self.instance.pk and self.instance.languages:
            if isinstance(self.instance.languages, list):
                self.fields['languages'].initial = self.instance.languages
            elif isinstance(self.instance.languages, str):
                self.fields['languages'].initial = [lang.strip() for lang in self.instance.languages.split(',')]

        # Auto-fill designation
        if self.instance and self.instance.pk and self.instance.personnel_type:
            designation_map = {
                'interpreter': 'INTERPRETER',
                'translator': 'TRANSLATOR',
                'icoordination': 'INTERPRETATION COORDINATION',
                'Tcoordination': 'TRANSLATION COORDINATION',
                'adminassistant': 'ADMINISTRATIVE ASSISTANT',
                'documentworkflowofficer': 'DOCUMENT WORKFLOW OFFICER',
                'conferencesystemtechnitians': 'CONFERENCE SYSTEM TECHNICIAN',
                'documentationdistributionanandcirculation': 'DOCUMENTATION DISTRIBUTION & CIRCULATION',
                'documentationreproductionandprinting': 'DOCUMENTATION REPRODUCTION & PRINTING',
                'both': 'INTERPRETER / TRANSLATOR',
            }
            self.fields['designation'].initial = designation_map.get(
                self.instance.personnel_type, 
                self.instance.personnel_type.upper().replace('_', ' ')
            )

        # Set translator_type / interpreter_type visibility
        if self.instance and self.instance.pk:
            if self.instance.personnel_type == 'translator':
                self.fields['translator_type'].required = True
                if self.instance.translator_type:
                    self.fields['translator_type'].initial = self.instance.translator_type
                self.fields['interpreter_type'].widget = forms.HiddenInput()
                self.fields['interpreter_type'].required = False
            elif self.instance.personnel_type == 'interpreter':
                self.fields['interpreter_type'].required = True
                if self.instance.interpreter_type:
                    self.fields['interpreter_type'].initial = self.instance.interpreter_type
                self.fields['translator_type'].widget = forms.HiddenInput()
                self.fields['translator_type'].required = False
            else:
                self.fields['translator_type'].widget = forms.HiddenInput()
                self.fields['translator_type'].required = False
                self.fields['interpreter_type'].widget = forms.HiddenInput()
                self.fields['interpreter_type'].required = False

    def clean_languages(self):
        languages = self.cleaned_data.get('languages', [])
        return list(languages)

    def clean_translator_type(self):
        """Validate translator_type is provided for translators"""
        personnel_type = self.cleaned_data.get('personnel_type')
        translator_type = self.cleaned_data.get('translator_type')
        
        if personnel_type == 'translator' and not translator_type:
            raise ValidationError("Translator type is required for translators (Freelance or Staff)")
        
        return translator_type

    def clean_interpreter_type(self):
        """Validate interpreter_type is provided for interpreters"""
        personnel_type = self.cleaned_data.get('personnel_type')
        interpreter_type = self.cleaned_data.get('interpreter_type')
        
        if personnel_type == 'interpreter' and not interpreter_type:
            raise ValidationError("Interpreter type is required for interpreters (Freelance or Staff)")
        
        return interpreter_type

    def save(self, commit=True):
        """Save the form with proper type handling"""
        instance = super().save(commit=False)
        
        personnel_type = self.cleaned_data.get('personnel_type')
        translator_type = self.cleaned_data.get('translator_type')
        interpreter_type = self.cleaned_data.get('interpreter_type')
        
        # Set the appropriate type based on personnel_type
        if personnel_type == 'translator':
            instance.translator_type = translator_type
            instance.interpreter_type = None
        elif personnel_type == 'interpreter':
            instance.interpreter_type = interpreter_type
            instance.translator_type = None
        else:
            instance.translator_type = None
            instance.interpreter_type = None
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance


# ---------- MEETING FORM ----------
class MeetingForm(forms.ModelForm):
    location = forms.ChoiceField(
        choices=AFRICAN_COUNTRY_CAPITALS,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        label='Location (Country - Capital)'
    )

    class Meta:
        model = Meeting
        fields = ['name', 'location', 'start_date', 'end_date', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ---------- DOCUMENT UPLOAD FORM ----------
class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['document_type', 'file', 'expiry_date', 'notes']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.personnel = kwargs.pop('personnel', None)
        super().__init__(*args, **kwargs)
        
        if self.personnel:
            # Get required documents for this personnel
            required_docs = self.personnel.get_required_documents()
            
            # Build choices based on required documents
            doc_choices = []
            doc_map = {
                'passport': 'Passport Copy',
                'loa': 'Letter of Assignment (LOA)',
                'boarding_pass': 'Boarding Pass',
                'payment_claim': 'Payment Claim',
                'ticket': 'Ticket',
                'ticket_receipt': 'Ticket Receipt',
                'invoice': 'Invoice',
                'photo': 'Passport Photo',
                'other': 'Other',
            }
            
            # Always include photo option
            doc_choices.append(('photo', 'Passport Photo'))
            
            for doc_type in required_docs:
                if doc_type in doc_map and doc_type != 'photo':
                    doc_choices.append((doc_type, doc_map[doc_type]))
            
            # Always include 'other'
            if ('other', 'Other') not in doc_choices:
                doc_choices.append(('other', 'Other'))
            
            self.fields['document_type'].choices = doc_choices
            self.fields['document_type'].empty_label = "Select document type..."

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > 5 * 1024 * 1024:
                raise ValidationError("File size cannot exceed 5MB.")
            allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
            ext = file.name.split('.')[-1].lower()
            if ext not in allowed_extensions:
                raise ValidationError(f"File type not allowed. Allowed: {', '.join(allowed_extensions)}")
        return file


# ---------- PAYMENT FORM ----------
class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = [
            'daily_rate', 'days_worked', 'travel_allowance',
            'accommodation_allowance', 'per_diem', 'special_allowance',
            'currency', 'notes'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.personnel = kwargs.pop('personnel', None)
        super().__init__(*args, **kwargs)
        if self.personnel:
            if self.personnel.personnel_type == 'interpreter':
                self.fields['daily_rate'].initial = 250
            else:
                self.fields['daily_rate'].initial = 200
        
        # Remove tax field from display since it's always 0
        self.fields.pop('tax', None)


# ---------- BULK UPLOAD FORM ----------
class BulkUploadForm(forms.Form):
    excel_file = forms.FileField(
        label='Excel File',
        help_text='Upload Excel file with personnel data',
        validators=[FileExtensionValidator(['xlsx', 'xls'])]
    )
    meeting = forms.ModelChoiceField(
        queryset=Meeting.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def clean_excel_file(self):
        file = self.cleaned_data.get('excel_file')
        if file:
            if file.size > 10 * 1024 * 1024:
                raise ValidationError("File size cannot exceed 10MB.")
        return file


# ---------- NOTIFICATION FORM ----------
class NotificationForm(forms.Form):
    personnel = forms.ModelMultipleChoiceField(
        queryset=Personnel.objects.filter(is_active=True),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'})
    )
    subject = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 10})
    )
    send_email = forms.BooleanField(
        required=False, 
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('subject') or not cleaned_data.get('message'):
            raise ValidationError("Both subject and message are required.")
        return cleaned_data
    
# personnel/forms.py — append

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    """Public contact form. Adds a honeypot field to block bots."""

    # Honeypot — real users never see or fill this.
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'autocomplete': 'off',
            'tabindex': '-1',
            'style': 'position:absolute;left:-9999px;',
        }),
    )

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your full name',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com',
                'required': True,
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional — e.g. +251 911 234 567',
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief subject line',
                'required': True,
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Describe your inquiry in detail…',
                'required': True,
            }),
        }

    def clean_website(self):
        """If the honeypot is filled, reject the submission."""
        value = self.cleaned_data.get('website', '')
        if value:
            raise forms.ValidationError("Spam detected.")
        return value

    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if len(message) < 10:
            raise forms.ValidationError("Please write at least 10 characters.")
        if len(message) > 5000:
            raise forms.ValidationError("Message is too long (max 5000 characters).")
        return message