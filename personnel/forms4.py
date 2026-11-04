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
# personnel/forms.py - PersonnelForm (COMPLETE WORKING VERSION)

# personnel/forms.py

class PersonnelForm(forms.ModelForm):
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
    
    class Meta:
        model = Personnel
        fields = [
            'first_name', 'middle_name', 'last_name', 'gender', 'date_of_birth',
            'nationality', 'email', 'phone', 'alternative_phone',
            'personnel_type', 'translator_type', 'designation', 'languages', 'city_departure',
            'meeting', 'notes', 'emergency_contact_name', 'emergency_contact_phone'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
            'designation': forms.TextInput(attrs={'readonly': 'readonly'}),
            'meeting': forms.Select(attrs={'class': 'form-select form-select-lg flex-grow-1'}),
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

        # CRITICAL FIX: Set translator_type initial value for editing
        if self.instance and self.instance.pk:
            if self.instance.personnel_type == 'translator':
                self.fields['translator_type'].required = True
                # Force the initial value from the instance
                if self.instance.translator_type:
                    self.fields['translator_type'].initial = self.instance.translator_type
                    self.initial['translator_type'] = self.instance.translator_type
            else:
                self.fields['translator_type'].required = False

    def clean_languages(self):
        languages = self.cleaned_data.get('languages', [])
        return list(languages)

    def clean_translator_type(self):
        """Validate translator_type is provided for translators"""
        personnel_type = self.cleaned_data.get('personnel_type')
        translator_type = self.cleaned_data.get('translator_type')
        
        print(f"===== clean_translator_type =====")
        print(f"personnel_type: {personnel_type}")
        print(f"translator_type: {translator_type}")
        print(f"=================================")
        
        if personnel_type == 'translator' and not translator_type:
            raise ValidationError("Translator type is required for translators (Freelance or Staff)")
        
        return translator_type

    def save(self, commit=True):
        """
        Save the form - FIXED VERSION
        """
        # Get the instance
        instance = super().save(commit=False)
        
        # Get values from cleaned_data
        personnel_type = self.cleaned_data.get('personnel_type')
        translator_type = self.cleaned_data.get('translator_type')
        
        print(f"===== DEBUG Form Save =====")
        print(f"Personnel Type from cleaned_data: '{personnel_type}'")
        print(f"Translator Type from cleaned_data: '{translator_type}'")
        print(f"Instance ID: {instance.id}")
        print(f"Instance personnel_type before save: '{instance.personnel_type}'")
        print(f"Instance translator_type before save: '{instance.translator_type}'")
        
        # CRITICAL: Set the personnel_type
        if personnel_type:
            instance.personnel_type = personnel_type
        
        # Set translator_type based on personnel_type
        if personnel_type == 'translator':
            instance.translator_type = translator_type
        else:
            instance.translator_type = None
        
        print(f"Instance personnel_type after setting: '{instance.personnel_type}'")
        print(f"Instance translator_type after setting: '{instance.translator_type}'")
        
        if commit:
            instance.save()
            self.save_m2m()
        
        print(f"Instance personnel_type after save: '{instance.personnel_type}'")
        print(f"Instance translator_type after save: '{instance.translator_type}'")
        print(f"===========================")
        
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
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


# ---------- DOCUMENT UPLOAD FORM ----------
class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['document_type', 'file', 'expiry_date', 'notes']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
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
                'other': 'Other',
            }
            
            for doc_type in required_docs:
                if doc_type in doc_map:
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
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.personnel = kwargs.pop('personnel', None)
        super().__init__(*args, **kwargs)
        if self.personnel:
            if self.personnel.personnel_type == 'interpreter':
                self.fields['daily_rate'].initial = 250
            else:
                self.fields['daily_rate'].initial = 200


# ---------- BULK UPLOAD FORM ----------
class BulkUploadForm(forms.Form):
    excel_file = forms.FileField(
        label='Excel File',
        help_text='Upload Excel file with personnel data',
        validators=[FileExtensionValidator(['xlsx', 'xls'])]
    )
    meeting = forms.ModelChoiceField(queryset=Meeting.objects.all())

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
    subject = forms.CharField(max_length=255)
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 10}))
    send_email = forms.BooleanField(required=False, initial=True)

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('subject') or not cleaned_data.get('message'):
            raise ValidationError("Both subject and message are required.")
        return cleaned_data