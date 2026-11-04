# personnel/management/commands/import_data.py

from django.core.management.base import BaseCommand
from django.db import transaction
from personnel.models import Personnel, Meeting
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import personnel data from Excel file'
    
    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to Excel file')
        parser.add_argument('--meeting', type=int, help='Meeting ID to assign')
    
    @transaction.atomic
    def handle(self, *args, **options):
        file_path = options['file_path']
        meeting_id = options.get('meeting')
        
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            self.stderr.write(f'Error reading file: {str(e)}')
            return
        
        if meeting_id:
            try:
                meeting = Meeting.objects.get(id=meeting_id)
            except Meeting.DoesNotExist:
                self.stderr.write(f'Meeting with ID {meeting_id} not found')
                return
        
        created_count = 0
        skipped_count = 0
        
        for _, row in df.iterrows():
            try:
                # Skip empty rows
                if pd.isna(row.get('First Name')):
                    continue
                
                # Determine personnel type
                designation = str(row.get('Designation/Assigment', '')).upper()
                if 'TRANSLATOR' in designation:
                    personnel_type = 'translator'
                elif 'INTERPRETER' in designation:
                    personnel_type = 'interpreter'
                else:
                    personnel_type = 'interpreter'
                
                # Handle Victor Afagbegee special case
                if 'Victor Afagbegee' in str(row.get('First Name', '')):
                    personnel_type = 'translator'
                    designation = 'English Translator'
                
                personnel = Personnel.objects.create(
                    first_name=str(row.get('First Name', '')).strip(),
                    last_name=str(row.get('Last Name', '')).strip(),
                    nationality=str(row.get('Nationality', '')).strip(),
                    personnel_type=personnel_type,
                    designation=designation,
                    city_departure=str(row.get('City of Departure', '')).strip(),
                    meeting=meeting if meeting_id else None,
                    is_active=True
                )
                
                created_count += 1
                self.stdout.write(f'Created: {personnel.full_name()}')
                
            except Exception as e:
                skipped_count += 1
                self.stderr.write(f'Error processing row {_+2}: {str(e)}')
        
        self.stdout.write(self.style.SUCCESS(
            f'Import complete: {created_count} created, {skipped_count} skipped'
        ))