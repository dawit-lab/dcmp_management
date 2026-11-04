# memos/management/commands/seed_departments.py

from django.core.management.base import BaseCommand
from memos.models import Department

class Command(BaseCommand):
    help = 'Seed default departments for memos'

    def handle(self, *args, **options):
        departments = [
            ('AU', 'African Union'),
            ('HR', 'Human Resources'),
            ('FIN', 'Finance'),
            ('IT', 'Information Technology'),
            ('OPS', 'Operations'),
            ('LEGAL', 'Legal'),
            ('ADMIN', 'Administration'),
            ('PR', 'Public Relations'),
            ('PROC', 'Procurement'),
            ('COMMS', 'Communications'),
            ('LOG', 'Logistics'),
            ('SEC', 'Security'),
        ]
        
        created_count = 0
        for code, name in departments:
            dept, created = Department.objects.get_or_create(
                code=code,
                defaults={'name': name, 'is_active': True}
            )
            if created:
                self.stdout.write(f'✓ Department created: {code} - {name}')
                created_count += 1
            else:
                self.stdout.write(f'Department already exists: {code} - {name}')
        
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully seeded {created_count} new departments'))