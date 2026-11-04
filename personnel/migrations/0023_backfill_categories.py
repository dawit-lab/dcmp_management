# personnel/migrations/00XX_backfill_categories.py

from django.db import migrations


def backfill_personnel_categories(apps, schema_editor):
    """
    Map old personnel_type/translator_type/interpreter_type to new
    profession + employment_basis + payment_method.
    """
    Personnel = apps.get_model('personnel', 'Personnel')

    for p in Personnel.objects.all():
        prof = 'interpreter'
        basis = 'na'
        method = 'per_meeting'

        old_type = p.personnel_type
        old_trans = p.translator_type
        old_interp = p.interpreter_type

        # --- Translators ---
        if old_type == 'translator':
            prof = 'translator'
            if old_trans == 'freelance':
                # Freelance translator from old system maps best to 'freelance' basis
                # (Word-count / per-assignment, like Online)
                basis = 'freelance'
                method = 'per_assignment'
            elif old_trans == 'staff':
                # Old 'staff' translator = short-term contract from roster
                basis = 'contract'
                method = 'salary_plus_dsa'
            else:
                # Fallback: treat as staff/contract
                basis = 'contract'
                method = 'salary_plus_dsa'

        # --- Interpreters ---
        elif old_type == 'interpreter':
            prof = 'interpreter'
            if old_interp == 'freelance':
                basis = 'freelance'
                method = 'per_meeting'
            elif old_interp == 'staff':
                basis = 'contract'
                method = 'salary_plus_dsa'
            else:
                basis = 'na'
                method = 'per_meeting'

        # --- Coordination and other types stay as-is ---
        elif old_type in ('icoordination', 'Tcoordination'):
            prof = old_type           # keeps 'icoordination' / 'Tcoordination'
            basis = 'na'
            method = 'per_meeting'
        else:
            prof = 'other'
            basis = 'na'
            method = 'per_meeting'

        p.profession = prof
        p.employment_basis = basis
        p.payment_method = method
        p.save(update_fields=['profession', 'employment_basis', 'payment_method'])

    # Backfill Payment.purpose: existing payments are almost certainly DSA
    Payment = apps.get_model('personnel', 'Payment')
    Payment.objects.all().update(purpose='dsa')


def reverse_backfill(apps, schema_editor):
    """
    Reverse is a no-op — we can't reliably reconstruct which rows were which
    because the source fields remain unchanged.
    """
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('personnel', '0022_documentrequirement_payment_purpose_and_more'),   # ← replace with your actual migration name
    ]
    operations = [
        migrations.RunPython(backfill_personnel_categories, reverse_backfill),
    ]