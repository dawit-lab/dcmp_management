# personnel/utils/payment_calculator.py

from decimal import Decimal
from ..models import Payment, Personnel, PaymentSetting

class PaymentCalculator:
    """Calculate payments for interpreters, translators, and coordination team"""
    
    # Default values in case settings don't exist
    DEFAULTS = {
        # Translator Rates
        'translator_freelance_daily': Decimal('252.00'),
        'translator_freelance_per_diem': Decimal('0.00'),
        'translator_staff_daily': Decimal('0.00'),
        'translator_staff_per_diem': Decimal('190.00'),
        
        # Interpreter Rates
        'interpreter_freelance_daily': Decimal('468.00'),
        'interpreter_freelance_per_diem': Decimal('190.00'),
        'interpreter_freelance_accommodation': Decimal('0.00'),
        'interpreter_freelance_travel': Decimal('468.00'),
        'interpreter_staff_daily': Decimal('0.00'),
        'interpreter_staff_per_diem': Decimal('190.00'),
        
        # Coordination Team Rates (All other types)
        'coordination_team_daily': Decimal('0.00'),
        'coordination_team_per_diem': Decimal('190.00'),
        
        # Allowances (Only for Freelance Interpreters)
        'terminal_expenses': Decimal('100.00'),
        'visa_fee': Decimal('50.00'),
        'other_allowance': Decimal('50.00'),
        'standby_daily_rate': Decimal('468.00'),
        'traveling_daily_rate': Decimal('468.00'),
        
        # Air Ticket Rates (Only for Freelance Interpreters)
        'air_ticket_base': Decimal('450.00'),
        'air_ticket_ethiopia': Decimal('500.00'),
        'air_ticket_nairobi': Decimal('400.00'),
        'air_ticket_accra': Decimal('350.00'),
        'air_ticket_lome': Decimal('300.00'),
        'air_ticket_long_distance': Decimal('600.00'),
        'long_distance_travel_bonus': Decimal('100.00'),
    }
    
    # Long distance cities for travel allowance
    LONG_DISTANCE_CITIES = [
        'DAR ES SALAAM', 'LILONGWE', 'MALABO', 'CAIRO',
        'NOUAKCHOTT', 'ALGIERS', 'ISTANBUL', 'BAMAKO',
        'ETHIOPIA', 'ADDIS ABABA'
    ]
    
    # Coordination team types
    COORDINATION_TYPES = [
        'icoordination',      # Interpretation coordination
        'Tcoordination',      # Translation coordination
        'adminassistant',     # Administrative Assistant
        'documentworkflowofficer',  # Document Workflow Officer
        'conferencesystemtechnitians',  # Conference System Technicians
        'documentationdistributionanandcirculation',  # Documentation Distribution and Circulation
        'documentationreproductionandprinting',  # Documentation Reproduction and Printing
        'both',               # Both interpreter and translator
    ]
    
    def __init__(self, personnel):
        self.personnel = personnel
        self.is_freelance = self._is_freelance()
        self.is_staff = self._is_staff()
        self.is_coordination = self._is_coordination()
        self.settings = self._load_settings()
        self.rate_config = self._get_rate_config()
    
    def _load_settings(self):
        """Load all settings from database with defaults"""
        settings = {}
        for key, default in self.DEFAULTS.items():
            try:
                # Try to get from database if PaymentSetting model exists
                settings[key] = PaymentSetting.get_value(key, default)
            except:
                settings[key] = default
        return settings
    
    def _is_freelance(self):
        """Check if personnel is a freelancer"""
        if self.personnel.personnel_type == 'translator':
            return self.personnel.translator_type == 'freelance'
        elif self.personnel.personnel_type == 'interpreter':
            return self.personnel.interpreter_type == 'freelance'
        return False
    
    def _is_staff(self):
        """Check if personnel is a staff"""
        if self.personnel.personnel_type == 'translator':
            return self.personnel.translator_type == 'staff'
        elif self.personnel.personnel_type == 'interpreter':
            return self.personnel.interpreter_type == 'staff'
        return False
    
    def _is_coordination(self):
        """Check if personnel is part of the coordination team"""
        return self.personnel.personnel_type in self.COORDINATION_TYPES
    
    def _get_rate_config(self):
        """
        Get the appropriate rate configuration based on personnel type and status
        
        GROUPS:
        1. TRANSLATORS: translators, both
        2. INTERPRETERS: interpreters
        3. COORDINATION TEAM: coordination, admin, document workflow, etc.
        
        Rules:
        - Freelance Translator: Only Salary (Daily Rate)
        - Staff Translator: Only DSA (Per Diem)
        - Freelance Interpreter: Salary + DSA + Accommodation + Travel + Standby + Traveling + Terminal + Visa + Air Ticket + Other
        - Staff Interpreter: Only DSA (Per Diem)
        - Coordination Team: Only DSA (Per Diem)
        """
        
        # ============================================================
        # GROUP 1: TRANSLATORS
        # ============================================================
        if self.personnel.personnel_type == 'translator':
            if self.is_freelance:
                # Freelance Translator: Only Salary (no DSA)
                return {
                    'group': 'Translator',
                    'daily_rate': self.settings.get('translator_freelance_daily', Decimal('252.00')),
                    'per_diem': Decimal('0.00'),
                    'accommodation': Decimal('0.00'),
                    'travel_allowance': Decimal('0.00'),
                    'has_full_benefits': False
                }
            else:
                # Staff Translator: ONLY DSA
                return {
                    'group': 'Translator',
                    'daily_rate': Decimal('0.00'),
                    'per_diem': self.settings.get('translator_staff_per_diem', Decimal('190.00')),
                    'accommodation': Decimal('0.00'),
                    'travel_allowance': Decimal('0.00'),
                    'has_full_benefits': False
                }
        
        # ============================================================
        # GROUP 2: INTERPRETERS
        # ============================================================
        elif self.personnel.personnel_type == 'interpreter':
            if self.is_freelance:
                # Freelance Interpreter: All benefits
                return {
                    'group': 'Interpreter',
                    'daily_rate': self.settings.get('interpreter_freelance_daily', Decimal('468.00')),
                    'per_diem': self.settings.get('interpreter_freelance_per_diem', Decimal('190.00')),
                    'accommodation': self.settings.get('interpreter_freelance_accommodation', Decimal('0.00')),
                    'travel_allowance': self.settings.get('interpreter_freelance_travel', Decimal('468.00')),
                    'has_full_benefits': True
                }
            else:
                # Staff Interpreter: ONLY DSA
                return {
                    'group': 'Interpreter',
                    'daily_rate': Decimal('0.00'),
                    'per_diem': self.settings.get('interpreter_staff_per_diem', Decimal('190.00')),
                    'accommodation': Decimal('0.00'),
                    'travel_allowance': Decimal('0.00'),
                    'has_full_benefits': False
                }
        
        # ============================================================
        # GROUP 3: COORDINATION TEAM
        # (All other types including both, coordination, admin, etc.)
        # ============================================================
        else:
            # Coordination Team: ONLY DSA (Per Diem)
            return {
                'group': 'Coordination Team',
                'daily_rate': self.settings.get('coordination_team_daily', Decimal('0.00')),
                'per_diem': self.settings.get('coordination_team_per_diem', Decimal('190.00')),
                'accommodation': Decimal('0.00'),
                'travel_allowance': Decimal('0.00'),
                'has_full_benefits': False
            }
    
    def calculate_payment(self, days_worked=3, standby_days=0, traveling_days=0):
        """
        Calculate complete payment based on personnel group
        
        GROUPS:
        1. TRANSLATORS:
           - Freelance: Salary (Daily Rate × Days Worked)
           - Staff: DSA (Per Diem × Days Worked)
        
        2. INTERPRETERS:
           - Freelance: Salary + DSA + Accommodation + Travel + Standby + Traveling + Terminal + Visa + Air Ticket + Other
           - Staff: DSA (Per Diem × Days Worked)
        
        3. COORDINATION TEAM:
           - All: DSA (Per Diem × Days Worked)
        
        No Tax for any group
        """
        # Base salary (only for freelance translator and freelance interpreter)
        base_payment = self.rate_config['daily_rate'] * days_worked
        
        # Get per diem rate
        per_diem_rate = self.rate_config['per_diem']
        
        # Per diem (DSA) - rate × days worked
        per_diem_total = per_diem_rate * days_worked
        
        # Check if this personnel type gets full benefits (only freelance interpreters)
        has_full_benefits = self.rate_config.get('has_full_benefits', False)
        group = self.rate_config.get('group', 'Unknown')
        
        # Only calculate extra benefits for freelance interpreters
        if has_full_benefits:
            # Travel allowance
            travel_allowance = self.calculate_travel_allowance()
            
            # Accommodation
            accommodation = self.rate_config['accommodation'] * days_worked
            
            # Standby days
            standby_rate = self.settings.get('standby_daily_rate', Decimal('468.00'))
            standby_payment = standby_rate * standby_days
            
            # Traveling days
            traveling_rate = self.settings.get('traveling_daily_rate', Decimal('468.00'))
            traveling_payment = traveling_rate * traveling_days
            
            # Terminal expenses
            terminal_expenses = self.settings.get('terminal_expenses', Decimal('24.00'))
            
            # Visa fee
            visa_fee = self.settings.get('visa_fee', Decimal('50.00'))
            
            # Other allowances
            other_allowance = self.settings.get('other_allowance', Decimal('50.00'))
            
            # Air ticket
            air_ticket = self.calculate_air_ticket()
        else:
            # No extra benefits for staff, translators, or coordination team
            travel_allowance = Decimal('0.00')
            accommodation = Decimal('0.00')
            standby_payment = Decimal('0.00')
            traveling_payment = Decimal('0.00')
            terminal_expenses = Decimal('0.00')
            visa_fee = Decimal('0.00')
            other_allowance = Decimal('0.00')
            air_ticket = Decimal('0.00')
        
        # Calculate totals (NO TAX)
        subtotal = (
            base_payment + 
            per_diem_total + 
            travel_allowance + 
            accommodation + 
            standby_payment + 
            traveling_payment + 
            terminal_expenses + 
            visa_fee + 
            air_ticket + 
            other_allowance
        )
        
        # No tax
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
        
        # Update payment fields
        payment.daily_rate = self.rate_config['daily_rate']
        payment.days_worked = days_worked
        payment.total_base = base_payment
        payment.travel_allowance = travel_allowance
        payment.accommodation_allowance = accommodation
        payment.per_diem = per_diem_total  # Total per diem (rate × days)
        payment.per_diem_rate = per_diem_rate  # Store the rate separately
        payment.special_allowance = (
            standby_payment + 
            traveling_payment + 
            terminal_expenses + 
            visa_fee + 
            air_ticket + 
            other_allowance
        )
        payment.subtotal = subtotal
        payment.tax = Decimal('0.00')
        payment.total_amount = total
        
        # Debug output
        print(f"===== PAYMENT CALCULATION =====")
        print(f"Personnel: {self.personnel.full_name()}")
        print(f"Type: {self.personnel.personnel_type}")
        print(f"Group: {group}")
        print(f"Subtype: {'Freelance' if self.is_freelance else 'Staff' if self.is_staff else 'Coordination'}")
        print(f"Has Full Benefits: {has_full_benefits}")
        print(f"Daily Rate: {self.rate_config['daily_rate']}")
        print(f"Per Diem Rate: {per_diem_rate}")
        print(f"Days Worked: {days_worked}")
        print(f"Per Diem Total (Rate × Days): {per_diem_total}")
        print(f"Base Payment: {base_payment}")
        print(f"Travel Allowance: {travel_allowance}")
        print(f"Accommodation: {accommodation}")
        print(f"Total: {total}")
        print(f"==============================")
        
        payment.save()
        
        return payment
    
    def calculate_travel_allowance(self):
        """Calculate travel allowance based on distance"""
        # Only freelance interpreters get travel allowance
        if not (self.personnel.personnel_type == 'interpreter' and self.is_freelance):
            return Decimal('0.00')
        
        base_travel = self.rate_config['travel_allowance']
        city = self.personnel.city_departure.upper()
        long_distance_bonus = self.settings.get('long_distance_travel_bonus', Decimal('100.00'))
        
        if any(city in long_city for long_city in self.LONG_DISTANCE_CITIES):
            return base_travel + long_distance_bonus
        elif city in ['ACCRA', 'GHANA', 'LOME', 'TOGO']:
            return base_travel - Decimal('50.00')
        else:
            return base_travel
    
    def calculate_air_ticket(self):
        """Calculate air ticket cost based on departure city using settings"""
        if not (self.personnel.personnel_type == 'interpreter' and self.is_freelance):
            return Decimal('0.00')
        
        city = self.personnel.city_departure.upper()
        
        # Get rates from settings
        rates = {
            'ethiopia': self.settings.get('air_ticket_ethiopia', Decimal('500.00')),
            'nairobi': self.settings.get('air_ticket_nairobi', Decimal('400.00')),
            'accra': self.settings.get('air_ticket_accra', Decimal('350.00')),
            'lome': self.settings.get('air_ticket_lome', Decimal('300.00')),
            'long_distance': self.settings.get('air_ticket_long_distance', Decimal('600.00')),
            'base': self.settings.get('air_ticket_base', Decimal('450.00')),
        }
        
        if city in ['ADDIS ABABA', 'ETHIOPIA']:
            return rates['ethiopia']
        elif city in ['NAIROBI', 'KENYA']:
            return rates['nairobi']
        elif city in ['ACCRA', 'GHANA']:
            return rates['accra']
        elif city in ['LOME', 'TOGO']:
            return rates['lome']
        elif any(city in long_city for long_city in self.LONG_DISTANCE_CITIES):
            return rates['long_distance']
        else:
            return rates['base']
    
    def get_payment_summary(self, days_worked=5, standby_days=0, traveling_days=0):
        """Get a detailed summary of the payment calculation"""
        payment = self.calculate_payment(days_worked, standby_days, traveling_days)
        
        # Recalculate the values for the summary
        has_full_benefits = self.rate_config.get('has_full_benefits', False)
        group = self.rate_config.get('group', 'Unknown')
        
        base_payment = self.rate_config['daily_rate'] * days_worked
        per_diem_rate = self.rate_config['per_diem']
        per_diem_total = per_diem_rate * days_worked
        
        # Only calculate extra benefits for freelance interpreters
        if has_full_benefits:
            travel_allowance = self.calculate_travel_allowance()
            accommodation = self.rate_config['accommodation'] * days_worked
            standby_rate = self.settings.get('standby_daily_rate', Decimal('468.00'))
            standby_payment = standby_rate * standby_days
            traveling_rate = self.settings.get('traveling_daily_rate', Decimal('468.00'))
            traveling_payment = traveling_rate * traveling_days
            terminal_expenses = self.settings.get('terminal_expenses', Decimal('100.00'))
            visa_fee = self.settings.get('visa_fee', Decimal('50.00'))
            air_ticket = self.calculate_air_ticket()
            other_allowance = self.settings.get('other_allowance', Decimal('50.00'))
        else:
            travel_allowance = Decimal('0.00')
            accommodation = Decimal('0.00')
            standby_payment = Decimal('0.00')
            traveling_payment = Decimal('0.00')
            terminal_expenses = Decimal('0.00')
            visa_fee = Decimal('0.00')
            air_ticket = Decimal('0.00')
            other_allowance = Decimal('0.00')
        
        summary = {
            'personnel': {
                'name': self.personnel.full_name(),
                'role': self.personnel.get_personnel_type_display(),
                'group': group,
                'type': 'Freelance' if self.is_freelance else 'Staff' if self.is_staff else 'Coordination',
                'city_departure': self.personnel.city_departure
            },
            'rates': {
                'daily_rate': self.rate_config['daily_rate'],
                'per_diem_rate': per_diem_rate,
                'accommodation': self.rate_config['accommodation'],
                'travel_allowance': self.rate_config['travel_allowance'],
                'has_full_benefits': has_full_benefits
            },
            'calculated': {
                'days_worked': days_worked,
                'standby_days': standby_days,
                'traveling_days': traveling_days,
                'base_salary': base_payment,
                'per_diem_total': per_diem_total,
                'travel_allowance': travel_allowance,
                'accommodation': accommodation,
                'standby_payment': standby_payment,
                'traveling_payment': traveling_payment,
                'terminal_expenses': terminal_expenses,
                'visa_fee': visa_fee,
                'air_ticket': air_ticket,
                'other_allowance': other_allowance,
                'subtotal': payment.subtotal,
                'tax': Decimal('0.00'),
                'total': payment.total_amount
            },
            'payment_status': payment.get_payment_status_display(),
            'currency': payment.currency
        }
        
        return summary