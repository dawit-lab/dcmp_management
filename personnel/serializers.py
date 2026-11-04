# personnel/serializers.py
from rest_framework import serializers
from .models import (
    Personnel, Document, Payment, Meeting,
    CommunicationLog, NotificationTemplate
)

class PersonnelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Personnel
        fields = '__all__'

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class MeetingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meeting
        fields = '__all__'

class CommunicationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunicationLog
        fields = '__all__'

class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = '__all__'


# personnel/serializers.py — append

from rest_framework import serializers
from .models import PersonnelExpense


# personnel/serializers.py — REPLACE the existing PersonnelExpenseSerializer

class PersonnelExpenseSerializer(serializers.ModelSerializer):
    personnel_name   = serializers.CharField(source='personnel.full_name', read_only=True)
    meeting_name     = serializers.CharField(source='meeting.name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    currency_display = serializers.CharField(source='get_currency_display', read_only=True)

    # Expose computed values for API consumers
    rate_based_subtotal = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True)
    rate_based_total    = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True)
    flat_total          = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = PersonnelExpense
        fields = [
            'id', 'personnel', 'personnel_name', 'meeting', 'meeting_name',
            'country', 'category', 'category_display', 'currency', 'currency_display',
            'number_of_days',
            'salary', 'dsa', 'travel_fee',
            'standby_days', 'terminal_expenses', 'visa_fees',
            'air_ticket', 'other',
            'rate_based_subtotal', 'rate_based_total', 'flat_total',
            'grand_total', 'is_locked',
            'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'grand_total', 'rate_based_subtotal', 'rate_based_total',
            'flat_total', 'created_by', 'created_at', 'updated_at',
        ]