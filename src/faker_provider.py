from faker import Faker
import random
import string

fake = Faker()
Faker.seed(42)  # reproducibility for testing

class FakeDataGenerator:
    """Generate realistic fake PII data."""
    
    _name_cache = {}
    _email_cache = {}
    _phone_cache = {}
    _ssn_cache = {}
    _credit_card_cache = {}
    _dob_cache = {}
    _address_cache = {}
    _company_cache = {}
    _ip_cache = {}
    
    @classmethod
    def reset_cache(cls):
        """Clear all caches (useful for fresh runs)."""
        cls._name_cache.clear()
        cls._email_cache.clear()
        cls._phone_cache.clear()
        cls._ssn_cache.clear()
        cls._credit_card_cache.clear()
        cls._dob_cache.clear()
        cls._address_cache.clear()
        cls._company_cache.clear()
        cls._ip_cache.clear()
    
    @classmethod
    def fake_name(cls, original: str) -> str:
        """Generate consistent fake name for original."""
        if original not in cls._name_cache:
            cls._name_cache[original] = fake.name()
        return cls._name_cache[original]
    
    @classmethod
    def fake_email(cls, original: str) -> str:
        """Generate consistent fake email for original."""
        if original not in cls._email_cache:
            cls._email_cache[original] = fake.email()
        return cls._email_cache[original]
    
    @classmethod
    def fake_phone(cls, original: str) -> str:
        """Generate fake phone number matching original format."""
        if original not in cls._phone_cache:
            # preserve format (indian vs international)
            if original.startswith('+91'):
                # indian format: +91 followed by 10 digits
                fake_num = fake.numerify(text='+91 ##########')
            elif original.startswith('+'):
                # international format
                fake_num = '+' + ''.join(random.choices(string.digits, k=len(original)-1))
            else:
                # plain number
                fake_num = fake.numerify(text='##########')
            cls._phone_cache[original] = fake_num
        return cls._phone_cache[original]
    
    @classmethod
    def fake_ssn(cls, original: str) -> str:
        """Generate fake SSN/Aadhar-like number."""
        if original not in cls._ssn_cache:
            # preserve format (9 or 12 digits)
            length = len(original.replace('-', '').replace(' ', ''))
            fake_num = ''.join(random.choices(string.digits, k=length))
            cls._ssn_cache[original] = fake_num
        return cls._ssn_cache[original]
    
    @classmethod
    def fake_credit_card(cls, original: str) -> str:
        """Generate fake credit card number."""
        if original not in cls._credit_card_cache:
            # generate valid-looking 16-digit card
            fake_card = fake.credit_card_number(card_type='visa')
            cls._credit_card_cache[original] = fake_card
        return cls._credit_card_cache[original]
    
    @classmethod
    def fake_dob(cls, original: str) -> str:
        """Generate fake date of birth preserving format."""
        if original not in cls._dob_cache:
            fake_date = fake.date_of_birth(minimum_age=18, maximum_age=80)
            # try to match original format
            if '/' in original:
                if original.startswith(original.split('/')[0]) and len(original.split('/')[0]) == 4:
                    formatted = fake_date.strftime('%Y/%m/%d')
                else:
                    formatted = fake_date.strftime('%d/%m/%Y')
            elif '-' in original:
                if original.startswith(original.split('-')[0]) and len(original.split('-')[0]) == 4:
                    formatted = fake_date.strftime('%Y-%m-%d')
                else:
                    formatted = fake_date.strftime('%d-%m-%Y')
            else:
                formatted = fake_date.strftime('%d/%m/%Y')
            cls._dob_cache[original] = formatted
        return cls._dob_cache[original]
    
    @classmethod
    def fake_address(cls, original: str) -> str:
        """Generate fake address."""
        if original not in cls._address_cache:
            cls._address_cache[original] = fake.address().replace('\n', ', ')
        return cls._address_cache[original]
    
    @classmethod
    def fake_company(cls, original: str) -> str:
        """Generate fake company name."""
        if original not in cls._company_cache:
            cls._company_cache[original] = fake.company()
        return cls._company_cache[original]
    
    @classmethod
    def fake_ip(cls, original: str) -> str:
        """Generate fake IP address."""
        if original not in cls._ip_cache:
            cls._ip_cache[original] = fake.ipv4()
        return cls._ip_cache[original]
