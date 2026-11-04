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

    # class Meta:
    #     model = Personnel
    #     fields = [
    #         'first_name', 'middle_name', 'last_name', 'gender', 'date_of_birth',
    #         'nationality', 'email', 'phone', 'alternative_phone',
    #         'personnel_type', 'designation', 'languages', 'city_departure',
    #         'meeting', 'notes', 'emergency_contact_name', 'emergency_contact_phone'
    #     ]
    #     widgets = {
    #         'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
    #         'notes': forms.Textarea(attrs={'rows': 4}),
    #         'designation': forms.TextInput(attrs={'readonly': 'readonly'}),
    #         'meeting': forms.Select(attrs={'class': 'form-select form-select-lg flex-grow-1'}),
    #     }

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

        # Auto-fill designation - COMPLETE MAPPING
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
                self.instance.personnel_type.upper().replace('_', ' ')  # fallback
            )

    def clean_languages(self):
        """Convert the list of selected languages to a JSON‑friendly list"""
        languages = self.cleaned_data.get('languages', [])
        return list(languages)

    # def clean_email(self):
    #     email = self.cleaned_data.get('email')
    #     if Personnel.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
    #         raise ValidationError("A personnel with this email already exists.")
    #     return email

        if self.instance and self.instance.pk:
                if self.instance.personnel_type == 'translator' and self.instance.translator_type:
                    self.fields['translator_type'].initial = self.instance.translator_type
            
            # Set translator_type required only for translators
                if self.instance and self.instance.pk and self.instance.personnel_type == 'translator':
                    self.fields['translator_type'].required = True
        
    def clean_translator_type(self):
            """Validate translator_type is provided for translators"""
            personnel_type = self.cleaned_data.get('personnel_type')
            translator_type = self.cleaned_data.get('translator_type')
            
            if personnel_type == 'translator' and not translator_type:
                raise ValidationError("Translator type is required for translators (Freelance or Staff)")
            
            return translator_type


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
# class DocumentUploadForm(forms.ModelForm):
#     class Meta:
#         model = Document
#         fields = ['document_type', 'file', 'expiry_date', 'notes']
#         widgets = {
#             'expiry_date': forms.DateInput(attrs={'type': 'date'}),
#             'notes': forms.Textarea(attrs={'rows': 3}),
#         }

#     def clean_file(self):
#         file = self.cleaned_data.get('file')
#         if file:
#             if file.size > 5 * 1024 * 1024:
#                 raise ValidationError("File size cannot exceed 5MB.")
#             allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
#             ext = file.name.split('.')[-1].lower()
#             if ext not in allowed_extensions:
#                 raise ValidationError(f"File type not allowed. Allowed: {', '.join(allowed_extensions)}")
#         return file

# personnel/forms.py

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
            # Filter document types based on personnel type
            required_docs = self.personnel.get_required_documents()
            allowed_types = [('other', 'Other')]  # Always allow 'other'
            
            for doc_type in required_docs:
                if doc_type != 'other':
                    # Get display name from the model's DOCUMENT_TYPES
                    for choice in Document.DOCUMENT_TYPES:
                        if choice[0] == doc_type:
                            allowed_types.append(choice)
                            break
            
            self.fields['document_type'].choices = allowed_types

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