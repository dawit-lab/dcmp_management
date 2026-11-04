# personnel/forms.py

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from decimal import Decimal
from .models import Personnel, Document, Payment, Meeting, UploadHistory, ContactMessage


# ---------- MEETING LOCATION (Country + Capital) ----------
# AFRICAN_COUNTRY_CAPITALS = [
#     ('Algeria - Algiers', 'Algeria - Algiers'),
#     ('Angola - Luanda', 'Angola - Luanda'),
#     ('Benin - Porto-Novo', 'Benin - Porto-Novo'),
#     ('Botswana - Gaborone', 'Botswana - Gaborone'),
#     ('Burkina Faso - Ouagadougou', 'Burkina Faso - Ouagadougou'),
#     ('Burundi - Bujumbra', 'Burundi - Bujumbra'),
#     ('Cabo Verde - Praia', 'Cabo Verde - Praia'),
#     ('Cameroon - Yaoundé', 'Cameroon - Yaoundé'),
#     ('Central African Republic - Bangui', 'Central African Republic - Bangui'),
#     ('Chad - N\'Djamena', 'Chad - N\'Djamena'),
#     ('Comoros - Moroni', 'Comoros - Moroni'),
#     ('Congo - Brazzaville', 'Congo - Brazzaville'),
#     ('Congo (DRC) - Kinshasa', 'Congo (DRC) - Kinshasa'),
#     ('Djibouti - Djibouti', 'Djibouti - Djibouti'),
#     ('Egypt - Cairo', 'Egypt - Cairo'),
#     ('Equatorial Guinea - Malabo', 'Equatorial Guinea - Malabo'),
#     ('Eritrea - Asmara', 'Eritrea - Asmara'),
#     ('Eswatini - Mbabane', 'Eswatini - Mbabane'),
#     ('Ethiopia - Addis Ababa', 'Ethiopia - Addis Ababa'),
#     ('Gabon - Libreville', 'Gabon - Libreville'),
#     ('Gambia - Banjul', 'Gambia - Banjul'),
#     ('Ghana - Accra', 'Ghana - Accra'),
#     ('Guinea - Conakry', 'Guinea - Conakry'),
#     ('Guinea-Bissau - Bissau', 'Guinea-Bissau - Bissau'),
#     ('Ivory Coast - Yamoussoukro', 'Ivory Coast - Yamoussoukro'),
#     ('Kenya - Nairobi', 'Kenya - Nairobi'),
#     ('Lesotho - Maseru', 'Lesotho - Maseru'),
#     ('Liberia - Monrovia', 'Liberia - Monrovia'),
#     ('Libya - Tripoli', 'Libya - Tripoli'),
#     ('Madagascar - Antananarivo', 'Madagascar - Antananarivo'),
#     ('Malawi - Lilongwe', 'Malawi - Lilongwe'),
#     ('Mali - Bamako', 'Mali - Bamako'),
#     ('Mauritania - Nouakchott', 'Mauritania - Nouakchott'),
#     ('Mauritius - Port Louis', 'Mauritius - Port Louis'),
#     ('Morocco - Rabat', 'Morocco - Rabat'),
#     ('Mozambique - Maputo', 'Mozambique - Maputo'),
#     ('Namibia - Windhoek', 'Namibia - Windhoek'),
#     ('Niger - Niamey', 'Niger - Niamey'),
#     ('Nigeria - Abuja', 'Nigeria - Abuja'),
#     ('Rwanda - Kigali', 'Rwanda - Kigali'),
#     ('Sao Tome and Principe - São Tomé', 'Sao Tome and Principe - São Tomé'),
#     ('Senegal - Dakar', 'Senegal - Dakar'),
#     ('Seychelles - Victoria', 'Seychelles - Victoria'),
#     ('Sierra Leone - Freetown', 'Sierra Leone - Freetown'),
#     ('Somalia - Mogadishu', 'Somalia - Mogadishu'),
#     ('South Africa - Pretoria', 'South Africa - Pretoria'),
#     ('South Sudan - Juba', 'South Sudan - Juba'),
#     ('Sudan - Khartoum', 'Sudan - Khartoum'),
#     ('Tanzania - Dodoma', 'Tanzania - Dodoma'),
#     ('Togo - Lomé', 'Togo - Lomé'),
#     ('Tunisia - Tunis', 'Tunisia - Tunis'),
#     ('Uganda - Kampala', 'Uganda - Kampala'),
#     ('Zambia - Lusaka', 'Zambia - Lusaka'),
#     ('Zimbabwe - Harare', 'Zimbabwe - Harare'),
# ]

# ---------- PERSONNEL NATIONALITY (Country only) ----------
AFRICAN_COUNTRIES = [
     ('N/A', 'N/A'),
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

# ---------- CITY OF DEPARTURE (Capital only) ----------
AFRICAN_CAPITALS = [
     ('N/A', 'N/A'),
    ('Addis Ababa', 'Addis Ababa'),
    ('Cairo', 'Cairo'),
    ('Nairobi', 'Nairobi'),
    ('Kigali', 'Kigali'),
    ('Kampala', 'Kampala'),
    ('Dar es Salaam', 'Dar es Salaam'),
    ('Dodoma', 'Dodoma'),
    ('Dakar', 'Dakar'),
    ('Accra', 'Accra'),
    ('Abuja', 'Abuja'),
    ('Pretoria', 'Pretoria'),
    ('Cape Town', 'Cape Town'),
    ('Lusaka', 'Lusaka'),
    ('Harare', 'Harare'),
    ('Kinshasa', 'Kinshasa'),
    ('Brazzaville', 'Brazzaville'),
    ('Luanda', 'Luanda'),
    ('Gaborone', 'Gaborone'),
    ('Windhoek', 'Windhoek'),
    ('Maputo', 'Maputo'),
    ('Lilongwe', 'Lilongwe'),
    ('Bujumbura', 'Bujumbura'),
    ('Khartoum', 'Khartoum'),
    ('Juba', 'Juba'),
    ('Mogadishu', 'Mogadishu'),
    ('Djibouti', 'Djibouti'),
    ('Asmara', 'Asmara'),
    ('Tripoli', 'Tripoli'),
    ('Tunis', 'Tunis'),
    ('Algiers', 'Algiers'),
    ('Rabat', 'Rabat'),
    ('Bamako', 'Bamako'),
    ('Niamey', 'Niamey'),
    ('Ouagadougou', 'Ouagadougou'),
    ('Conakry', 'Conakry'),
    ('Bissau', 'Bissau'),
    ('Banjul', 'Banjul'),
    ('Freetown', 'Freetown'),
    ('Monrovia', 'Monrovia'),
    ('Yamoussoukro', 'Yamoussoukro'),
    ('Lome', 'Lome'),
    ('Porto-Novo', 'Porto-Novo'),
    ('Yaoundé', 'Yaoundé'),
    ('Libreville', 'Libreville'),
    ('Malabo', 'Malabo'),
    ('Bangui', 'Bangui'),
    ('NDjamena', 'NDjamena'),
    ('Kinshasa', 'Kinshasa'),
    ('Moroni', 'Moroni'),
    ('Antananarivo', 'Antananarivo'),
    ('Port Louis', 'Port Louis'),
    ('Victoria', 'Victoria'),
    ('Praia', 'Praia'),
    ('São Tomé', 'São Tomé'),
    ('Maseru', 'Maseru'),
    ('Mbabane', 'Mbabane'),
]

# ============================================================
# PERSONNEL FORM
# ============================================================

class PersonnelForm(forms.ModelForm):
    """
    Create / edit form for Personnel.

    Authoritative classification fields: profession, employment_basis, payment_method.
    Legacy fields personnel_type / translator_type / interpreter_type are kept
    on the form as HiddenInput and synced from the new fields in save(),
    so older code paths keep working.
    """

    nationality = forms.ChoiceField(
        choices=AFRICAN_COUNTRIES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        label='Nationality',
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
        help_text="Select the languages spoken",
    )

    photo = forms.ImageField(
        required=False,
        label='Passport Photo',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
        }),
        help_text='Upload a passport-style photo (JPG, PNG, GIF - max 5MB)',
    )

    class Meta:
        model = Personnel
        fields = [
            'first_name', 'middle_name', 'last_name', 'gender', 'date_of_birth',
            'nationality', 'email', 'phone', 'alternative_phone',

            # NEW canonical classification
            'profession', 'employment_basis', 'payment_method',

            # NOTE: personnel_type / translator_type / interpreter_type
            # are NOT on the form. They are derived from profession +
            # employment_basis inside save().

            'designation', 'languages', 'city_departure',
            'meeting', 'notes', 'emergency_contact_name', 'emergency_contact_phone',
            'travelled_abroad', 'travel_notes',
            'photo',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'alternative_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'city_departure': forms.TextInput(attrs={'class': 'form-control'}),

            # NEW
            'profession':       forms.Select(attrs={'class': 'form-select'}),
            'employment_basis': forms.Select(attrs={'class': 'form-select'}),
            'payment_method':   forms.Select(attrs={'class': 'form-select'}),

            # Legacy (hidden)
            # 'personnel_type':   forms.HiddenInput(),
            # 'translator_type':  forms.HiddenInput(),
            # 'interpreter_type': forms.HiddenInput(),

            'designation': forms.TextInput(attrs={'class': 'form-control'}),
            'meeting': forms.Select(attrs={'class': 'form-select form-select-lg flex-grow-1'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),

            'travelled_abroad': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'travel_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),

        }

    # ------------------------------------------------------------
    # INIT — seed initial values for edit
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        instance = self.instance

        # Nationality fallback: if stored value isn't in the list, add it.
        if instance and instance.pk and instance.nationality:
            current = instance.nationality
            values = [choice[0] for choice in self.fields['nationality'].choices]
            if current not in values:
                self.fields['nationality'].choices = (
                    list(self.fields['nationality'].choices) + [(current, current)]
                )

        # Languages: seed initial from instance JSON list/str
        if instance and instance.pk and instance.languages:
            if isinstance(instance.languages, list):
                self.fields['languages'].initial = instance.languages
            elif isinstance(instance.languages, str):
                self.fields['languages'].initial = [
                    lang.strip() for lang in instance.languages.split(',') if lang.strip()
                ]

        # Designation: auto-fill from profession on edit
        if instance and instance.pk and instance.profession:
            designation_map = {
                'interpreter': 'INTERPRETER',
                'translator': 'TRANSLATOR',
                'icoordination': 'INTERPRETATION COORDINATION',
                'Tcoordination': 'TRANSLATION COORDINATION',
                'adminassistant': 'ADMINISTRATIVE ASSISTANT',
                'documentworkflowofficer': 'DOCUMENT WORKFLOW OFFICER',
                'conferencesystemtechnitians': 'CONFERENCE SYSTEM TECHNICIAN',
                'documentationdistributionandcirculation': 'DOCUMENTATION DISTRIBUTION & CIRCULATION',
                'documentationreproductionandprinting': 'DOCUMENTATION REPRODUCTION & PRINTING',
                'other': 'OTHER',
            }
            self.fields['designation'].initial = designation_map.get(
                instance.profession,
                instance.profession.upper().replace('_', ' '),
            )

    # ------------------------------------------------------------
    # CLEAN
    # ------------------------------------------------------------
    def clean_languages(self):
        return list(self.cleaned_data.get('languages', []))

    def clean_photo(self):
        """
        On edit, an empty FileField means 'keep existing' — return None so
        save() knows not to touch the DB value.
        """
        photo = self.cleaned_data.get('photo')
        if photo is False:
            return None
        return photo

    # ------------------------------------------------------------
    # SAVE — keep new + legacy fields in sync, preserve photo on edit
    # ------------------------------------------------------------
    def save(self, commit=True):
        instance = super().save(commit=False)

        # --- Photo preservation on edit ---
        # If this is an existing row and no new file was uploaded,
        # re-attach the stored photo so we don't wipe it.
        if instance.pk:
            new_photo = self.cleaned_data.get('photo')
            if not new_photo:
                try:
                    existing = Personnel.objects.get(pk=instance.pk)
                    instance.photo = existing.photo
                except Personnel.DoesNotExist:
                    pass

        # --- Sync new canonical fields ---
        profession = self.cleaned_data.get('profession') or instance.profession
        employment_basis = (
            self.cleaned_data.get('employment_basis') or instance.employment_basis
        )
        payment_method = (
            self.cleaned_data.get('payment_method') or instance.payment_method
        )

        instance.profession = profession
        instance.employment_basis = employment_basis
        instance.payment_method = payment_method

        # --- Mirror into legacy personnel_type ---
        instance.personnel_type = profession

        # --- Mirror into legacy translator_type / interpreter_type ---
        if profession == 'translator':
            if employment_basis == 'freelance':
                instance.translator_type = 'freelance'
            elif employment_basis in ('regular', 'contract', 'daily'):
                instance.translator_type = 'staff'
            else:
                instance.translator_type = None
            instance.interpreter_type = None

        elif profession == 'interpreter':
            if employment_basis == 'freelance':
                instance.interpreter_type = 'freelance'
            elif employment_basis in ('regular', 'contract', 'daily'):
                instance.interpreter_type = 'staff'
            else:
                instance.interpreter_type = None
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
        choices=AFRICAN_CAPITALS,
        #choices=AFRICAN_COUNTRY_CAPITALS,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        label='Location (Country - Capital)',
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
    """
    Form to upload (or replace) a Document for a Personnel.

    The document_type dropdown always exposes the full set of document
    types — not just the ones currently required for this person — so
    admins can upload ad-hoc documents (e.g. an AP or a CP) without
    having to change the DocumentRequirement rules first.
    """

    # Canonical ordering shown in the dropdown.
    # (value, label) — value must match Document.DOCUMENT_TYPES.
    ALL_DOCUMENT_CHOICES = [
        ('passport',       'Passport Copy'),
        ('loa',            'Letter of Assignment (LOA)'),
        ('boarding_pass',  'Boarding Pass'),
        ('ticket',         'Ticket'),
        ('ticket_receipt', 'Ticket Receipt'),
        ('invoice',        'Invoice'),
        ('payment_claim',  'Payment Claim'),
        ('cp',             'Certificate of Performance'),
        ('ap',             'Authorization of Payment'),
        ('photo',          'Passport Photo'),
        ('other',          'Other'),
    ]

    class Meta:
        model = Document
        fields = ['document_type', 'file', 'expiry_date', 'notes']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        # `personnel` is optional. If supplied, we could restrict the list,
        # but per the current requirement we always show the full list.
        self.personnel = kwargs.pop('personnel', None)
        super().__init__(*args, **kwargs)

        # Always show all document types.
        self.fields['document_type'].choices = self.ALL_DOCUMENT_CHOICES
        self.fields['document_type'].empty_label = "Select document type..."

        # Bootstrap-friendly class on the select
        self.fields['document_type'].widget.attrs.update({'class': 'form-select'})

        # If we're replacing an existing document, preselect its type
        # and lock the dropdown so the type can't be changed accidentally.
        if self.instance and self.instance.pk:
            self.fields['document_type'].initial = self.instance.document_type
            self.fields['document_type'].disabled = True

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > 5 * 1024 * 1024:
                raise ValidationError("File size cannot exceed 5MB.")
            allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
            ext = file.name.split('.')[-1].lower()
            if ext not in allowed_extensions:
                raise ValidationError(
                    f"File type not allowed. Allowed: {', '.join(allowed_extensions)}"
                )
        return file


# ---------- PAYMENT FORM ----------
class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = [
            'daily_rate', 'days_worked', 'travel_allowance',
            'accommodation_allowance', 'per_diem', 'special_allowance',
            'currency', 'notes',
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.personnel = kwargs.pop('personnel', None)
        super().__init__(*args, **kwargs)
        if self.personnel:
            if self.personnel.profession == 'interpreter':
                self.fields['daily_rate'].initial = 250
            else:
                self.fields['daily_rate'].initial = 200


# ---------- BULK UPLOAD FORM ----------
class BulkUploadForm(forms.Form):
    excel_file = forms.FileField(
        label='Excel File',
        help_text='Upload Excel file with personnel data',
        validators=[FileExtensionValidator(['xlsx', 'xls'])],
    )
    meeting = forms.ModelChoiceField(
        queryset=Meeting.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
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
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
    )
    subject = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
    )
    send_email = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('subject') or not cleaned_data.get('message'):
            raise ValidationError("Both subject and message are required.")
        return cleaned_data


# ---------- CONTACT FORM ----------
class ContactForm(forms.ModelForm):
    """Public contact form with honeypot."""

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
    
# personnel/forms.py — append this form

from .models import PersonnelExpense


# personnel/forms.py — REPLACE the existing PersonnelExpenseForm

class PersonnelExpenseForm(forms.ModelForm):
    """
    Manual expense entry form.

    `number_of_days` multiplies Salary, DSA and Travel Fee on the server
    (in PersonnelExpense.save()). The client-side JS total is only for
    live preview — the DB value is always authoritative.
    """

    class Meta:
        model = PersonnelExpense
        fields = [
            'personnel', 'meeting', 'country', 'category', 'currency',
            'number_of_days',
            'salary', 'dsa', 'travel_fee',
            'standby_days', 'terminal_expenses', 'visa_fees',
            'air_ticket', 'other',
            'is_locked',
        ]
        widgets = {
            'personnel':         forms.Select(attrs={'class': 'form-select'}),
            'meeting':           forms.Select(attrs={'class': 'form-select'}),
            'country':           forms.TextInput(attrs={
                                     'class': 'form-control',
                                     'placeholder': 'e.g., Ethiopia — Addis Ababa'}),
            'category':          forms.Select(attrs={'class': 'form-select'}),
            'currency':          forms.Select(attrs={'class': 'form-select'}),

            # Number of days — default 1
            'number_of_days':    forms.NumberInput(attrs={
                                     'class': 'form-control expense-days',
                                     'step': '0.5', 'min': '0.5',
                                     'value': '1'}),  # initial via form __init__

            # Rate-based fields (multiplied)
            'salary':            forms.NumberInput(attrs={
                                     'class': 'form-control expense-input',
                                     'step': '0.01', 'min': '0',
                                     'data-rate-based': 'true'}),
            'dsa':               forms.NumberInput(attrs={
                                     'class': 'form-control expense-input',
                                     'step': '0.01', 'min': '0',
                                     'data-rate-based': 'true'}),
            'travel_fee':        forms.NumberInput(attrs={
                                     'class': 'form-control expense-input',
                                     'step': '0.01', 'min': '0',
                                     'data-rate-based': 'true'}),

            # Flat fields
            'standby_days':      forms.NumberInput(attrs={
                                     'class': 'form-control expense-input',
                                     'step': '0.01', 'min': '0'}),
            'terminal_expenses': forms.NumberInput(attrs={
                                     'class': 'form-control expense-input',
                                     'step': '0.01', 'min': '0'}),
            'visa_fees':         forms.NumberInput(attrs={
                                     'class': 'form-control expense-input',
                                     'step': '0.01', 'min': '0'}),
            'air_ticket':        forms.NumberInput(attrs={
                                     'class': 'form-control expense-input',
                                     'step': '0.01', 'min': '0'}),
            'other':             forms.NumberInput(attrs={
                                     'class': 'form-control expense-input',
                                     'step': '0.01', 'min': '0'}),

            'is_locked':         forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Default number_of_days to 1 on create
        if not self.instance.pk:
            self.fields['number_of_days'].initial = 1

        # Non-admins can't lock
        if self.user and not self.user.is_staff:
            self.fields['is_locked'].widget = forms.HiddenInput()

        # Pre-fill meeting from personnel on create
        if not self.instance.pk and not self.initial.get('meeting'):
            personnel_id = self.initial.get('personnel')
            if personnel_id:
                try:
                    p = Personnel.objects.get(pk=personnel_id)
                    self.fields['meeting'].initial = p.meeting
                except Personnel.DoesNotExist:
                    pass

    def clean_number_of_days(self):
        days = self.cleaned_data.get('number_of_days')
        if days is None or days <= 0:
            return Decimal('1.00')
        return days

    def clean(self):
        cleaned = super().clean()

        # Block edits to locked records for non-admins
        if (self.instance.pk and self.instance.is_locked
                and self.user and not self.user.is_staff):
            raise ValidationError(
                "This expense record is locked. Only an administrator can modify it."
            )

        # Auto-fill meeting from personnel
        personnel = cleaned.get('personnel')
        if personnel and not cleaned.get('meeting') and personnel.meeting:
            cleaned['meeting'] = personnel.meeting

        return cleaned
    
from .models import PersonnelMaster

class PersonnelMasterPickerForm(forms.Form):
    """
    Dropdown that lists every active master record.
    The rest of the fields are auto-filled by JavaScript.
    """
    first_name = forms.ModelChoiceField(
        queryset=PersonnelMaster.objects.filter(is_active=True).order_by('first_name'),
        empty_label="Select a first name...",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_master_first_name'}),
        label="First Name",
    )

from .models import PersonnelMaster


class PersonnelMasterForm(forms.ModelForm):
    """Form used inside the Add-to-Master-List modal."""

    nationality = forms.ChoiceField(
        choices=AFRICAN_COUNTRIES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        label='Nationality',
    )

    # city_departure = forms.ChoiceField(
    #     choices=AFRICAN_COUNTRY_CAPITALS,   # reuse the Country–Capital list
    #     widget=forms.Select(attrs={'class': 'form-select'}),
    #     required=False,
    #     label='City of Departure',
    #)

    city_departure = forms.ChoiceField(
        choices=AFRICAN_CAPITALS,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        label='City of Departure',
    )

    class Meta:
        model = PersonnelMaster
        fields = [
            'first_name', 'middle_name', 'last_name',
            'gender', 'date_of_birth', 'nationality',
            'email', 'phone', 'alternate_phone',
            'city_departure',
        ]
        widgets = {
            'first_name':      forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name':     forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':       forms.TextInput(attrs={'class': 'form-control'}),
            'gender':          forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth':   forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            # nationality + city_departure are overridden above
            'email':           forms.EmailInput(attrs={'class': 'form-control'}),
            'phone':           forms.TextInput(attrs={'class': 'form-control'}),
            'alternate_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }