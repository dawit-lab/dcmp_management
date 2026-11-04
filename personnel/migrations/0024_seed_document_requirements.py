# personnel/migrations/00XX_seed_document_requirements.py

from django.db import migrations


# The complete rule set, exactly as confirmed above
REQUIREMENTS = [
    # 1. Regular translator
    # routine: none
    ('translator', 'regular', 'travel', 'passport'),
    ('translator', 'regular', 'travel', 'ticket'),
    ('translator', 'regular', 'travel', 'boarding_pass'),

    # 2. Staff translator (contract)
    ('translator', 'contract', 'routine', 'loa'),
    ('translator', 'contract', 'routine', 'cp'),
    ('translator', 'contract', 'routine', 'ap'),
    ('translator', 'contract', 'routine', 'payment_claim'),
    ('translator', 'contract', 'travel', 'passport'),
    ('translator', 'contract', 'travel', 'ticket'),
    ('translator', 'contract', 'travel', 'boarding_pass'),

    # 3. Online translator (freelance)
    ('translator', 'freelance', 'routine', 'payment_claim'),
    ('translator', 'freelance', 'routine', 'invoice'),
    # no travel

    # 4. Regular interpreter
    ('interpreter', 'regular', 'travel', 'passport'),
    ('interpreter', 'regular', 'travel', 'ticket'),
    ('interpreter', 'regular', 'travel', 'boarding_pass'),

    # 5. Staff interpreter (contract)
    ('interpreter', 'contract', 'routine', 'loa'),
    ('interpreter', 'contract', 'routine', 'cp'),
    ('interpreter', 'contract', 'routine', 'ap'),
    ('interpreter', 'contract', 'routine', 'payment_claim'),
    ('interpreter', 'contract', 'travel', 'passport'),
    ('interpreter', 'contract', 'travel', 'ticket'),
    ('interpreter', 'contract', 'travel', 'boarding_pass'),

    # 6. Daily interpreter
    ('interpreter', 'daily', 'routine', 'loa'),
    ('interpreter', 'daily', 'routine', 'cp'),
    ('interpreter', 'daily', 'routine', 'ap'),
    ('interpreter', 'daily', 'routine', 'payment_claim'),
    ('interpreter', 'daily', 'travel', 'passport'),
    ('interpreter', 'daily', 'travel', 'ticket'),
    ('interpreter', 'daily', 'travel', 'boarding_pass'),

    # ---- Fallback: coordination + other types ----
    # Use a blank employment_basis so the rule applies to all
    ('icoordination', '', 'routine', 'passport'),
    ('icoordination', '', 'routine', 'boarding_pass'),
    ('icoordination', '', 'routine', 'ticket'),
    ('icoordination', '', 'routine', 'ticket_receipt'),
    ('Tcoordination', '', 'routine', 'passport'),
    ('Tcoordination', '', 'routine', 'boarding_pass'),
    ('Tcoordination', '', 'routine', 'ticket'),
    ('Tcoordination', '', 'routine', 'ticket_receipt'),
]


def seed_requirements(apps, schema_editor):
    DocumentRequirement = apps.get_model('personnel', 'DocumentRequirement')

    # Clear any existing rows to make the migration idempotent
    DocumentRequirement.objects.all().delete()

    for profession, basis, context, doc_type in REQUIREMENTS:
        DocumentRequirement.objects.create(
            profession=profession,
            employment_basis=basis,
            context=context,
            document_type=doc_type,
            is_required=True,
        )


def unseed_requirements(apps, schema_editor):
    DocumentRequirement = apps.get_model('personnel', 'DocumentRequirement')
    DocumentRequirement.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('personnel', '0023_backfill_categories'),   # the previous migration
    ]
    operations = [
        migrations.RunPython(seed_requirements, unseed_requirements),
    ]