# dcmp_management/celery.py

import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dcmp_management.settings')

app = Celery('dcmp_management')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Scheduled tasks
app.conf.beat_schedule = {
    'send-daily-reminders': {
        'task': 'personnel.tasks.send_daily_document_reminders',
        'schedule': crontab(hour=9, minute=0),  # 9 AM daily
    },
    'send-payment-reminders': {
        'task': 'personnel.tasks.send_payment_reminders',
        'schedule': crontab(hour=10, minute=0),  # 10 AM daily
    },
    'check-expiring-documents': {
        'task': 'personnel.tasks.check_expiring_documents',
        'schedule': crontab(hour=8, minute=0),  # 8 AM daily
    },
}