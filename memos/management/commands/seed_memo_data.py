from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from memos.models import Department, MemoType, MemoCategory

class Command(BaseCommand):
    help = 'Seed initial data for memos'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding memo data...')
        
        # Create Departments
        departments = [
            {'name': 'Human Resources', 'code': 'HR'},
            {'name': 'Finance', 'code': 'FIN'},
            {'name': 'Administration', 'code': 'ADMIN'},
            {'name': 'Procurement', 'code': 'PROC'},
            {'name': 'Legal', 'code': 'LEGAL'},
            {'name': 'IT Services', 'code': 'IT'},
            {'name': 'Communications', 'code': 'COMM'},
            {'name': 'Research', 'code': 'RES'},
            {'name': 'Operations', 'code': 'OPS'},
            {'name': 'Executive Office', 'code': 'EXEC'},
        ]
        
        for dept_data in departments:
            Department.objects.get_or_create(
                code=dept_data['code'],
                defaults={
                    'name': dept_data['name'],
                    'description': f"{dept_data['name']} Department",
                    'is_active': True
                }
            )
        self.stdout.write(self.style.SUCCESS(f'Created {len(departments)} departments'))
        
        # Create Memo Types
        memo_types = [
            {'name': 'Official Memo', 'code': 'OFFICIAL'},
            {'name': 'Internal Memo', 'code': 'INTERNAL'},
            {'name': 'Confidential Memo', 'code': 'CONFIDENTIAL'},
            {'name': 'Circular', 'code': 'CIRCULAR'},
            {'name': 'Request', 'code': 'REQUEST'},
            {'name': 'Response', 'code': 'RESPONSE'},
            {'name': 'Notification', 'code': 'NOTIFICATION'},
        ]
        
        for mt_data in memo_types:
            MemoType.objects.get_or_create(
                code=mt_data['code'],
                defaults={'name': mt_data['name'], 'description': f"{mt_data['name']} type"}
            )
        self.stdout.write(self.style.SUCCESS(f'Created {len(memo_types)} memo types'))
        
        # Create Memo Categories
        memo_categories = [
            {'name': 'Interpreter Nomination', 'category_type': 'interpreter_nomination'},
            {'name': 'Translator Nomination', 'category_type': 'translator_nomination'},
            {'name': 'Both Interpreter & Translator Nomination', 'category_type': 'both_nomination'},
            {'name': 'Interpreter List Preparation', 'category_type': 'interpreter_list'},
            {'name': 'Translator List Preparation', 'category_type': 'translator_list'},
            {'name': 'Both Interpreter & Translator List Preparation', 'category_type': 'both_list'},
            {'name': 'General Request', 'category_type': 'general_request'},
            {'name': 'Information', 'category_type': 'information'},
            {'name': 'Circular', 'category_type': 'circular'},
            {'name': 'Other', 'category_type': 'other'},
        ]
        
        for cat_data in memo_categories:
            MemoCategory.objects.get_or_create(
                category_type=cat_data['category_type'],
                defaults={'name': cat_data['name'], 'description': f"{cat_data['name']} category"}
            )
        self.stdout.write(self.style.SUCCESS(f'Created {len(memo_categories)} memo categories'))
        
        self.stdout.write(self.style.SUCCESS('Memo data seeding completed!'))