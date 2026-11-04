# personnel/utils/payment_calculator.py

from decimal import Decimal
from ..models import Payment, Personnel

class PaymentCalculator:
    """Calculate payments for interpreters and translators"""
    
    RATES = {
        'interpreter': {
            'daily_rate': Decimal('468.00'),
            'per_diem': Decimal('75.00'),
            'accommodation': Decimal('150.00'),
            'travel_allowance': Decimal('468.00')
        },
        'translator': {
            'daily_rate': Decimal('252.00'),
            'per_diem': Decimal('00.00'),
            'accommodation': Decimal('00.00'),
            'travel_allowance': Decimal('00.00')
        }
    }
    
    LONG_DISTANCE_CITIES = [
        'DAR ES SALAAM', 'LILONGWE', 'MALABO', 'CAIRO',
        'NOUAKCHOTT', 'ALGIERS', 'ISTANBUL', 'BAMAKO',
        'ETHIOPIA', 'ADDIS ABABA'
    ]
    
    def __init__(self, personnel):
        self.personnel = personnel
        self.rate_config = self.RATES.get(
            personnel.personnel_type, 
            self.RATES['interpreter']
        )
    
    def calculate_payment(self, days_worked=2):
        """Calculate complete payment"""
        # Base payment
        base_payment = self.rate_config['daily_rate'] * days_worked
        
        # Per diem
        per_diem = self.rate_config['per_diem'] * days_worked
        
        # Travel allowance
        travel_allowance = self.calculate_travel_allowance()
        
        # Accommodation
        accommodation = self.rate_config['accommodation'] * days_worked
        
        # Special allowances
        special_allowance = self.calculate_special_allowance()
        
        # Calculate totals
        subtotal = base_payment + per_diem + travel_allowance + accommodation + special_allowance
        #tax = subtotal * Decimal('0.05')  # 5% tax
        #total = subtotal + tax
        total = subtotal 
        
        # Create or update payment record
        payment, created = Payment.objects.get_or_create(
            personnel=self.personnel,
            defaults={
                'meeting': self.personnel.meeting,
                'role_type': self.personnel.personnel_type,
                'days_worked': days_worked
            }
        )
        
        payment.daily_rate = self.rate_config['daily_rate']
        payment.days_worked = days_worked
        payment.total_base = base_payment
        payment.travel_allowance = travel_allowance
        payment.accommodation_allowance = accommodation
        payment.per_diem = per_diem
        payment.special_allowance = special_allowance
        payment.subtotal = subtotal
        #payment.tax = tax
        payment.total_amount = total
        payment.save()
        
        return payment
    
    def calculate_travel_allowance(self):
        """Calculate travel allowance based on distance"""
        base_travel = self.rate_config['travel_allowance']
        city = self.personnel.city_departure.upper()
        
        # Long distance check
        if any(city in long_city for long_city in self.LONG_DISTANCE_CITIES):
            return base_travel + Decimal('100.00')
        elif city in ['ACCRA', 'GHANA', 'LOME, TOGO']:
            return base_travel - Decimal('50.00')
        else:
            return base_travel
    
    def calculate_special_allowance(self):
        """Calculate special allowances for specific cases"""
        # Victor Afagbegee - Translator based in Ethiopia
        if 'Victor' in self.personnel.first_name and self.personnel.personnel_type == 'translator':
            return Decimal('100.00')
        return Decimal('0.00')