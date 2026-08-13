import re
import spacy
from typing import List, Tuple, Dict, Set
from dataclasses import dataclass

@dataclass
class PIIMatch:
    """Represents a detected PII entity."""
    text: str
    pii_type: str
    start: int
    end: int
    confidence: float
    method: str  # 'regex', 'ner', or 'hybrid'

# Non-PII words, labels, and acronyms that should never be redacted as PII entities
NON_PII_WORDS: Set[str] = {
    'PII', 'SSN', 'DOB', 'PAN', 'IP', 'IPV4', 'IPV6', 'MAC', 'OTP', 'API',
    'INR', 'USD', 'EUR', 'GBP', 'ID', 'GOV_ID', 'NETWORK', 'EMAIL', 'PHONE',
    'MOBILE', 'FAX', 'TEL', 'ADDRESS', 'CITY', 'STATE', 'COUNTRY', 'ZIP',
    'TAX', 'PASSPORT', 'LICENSE', 'DRIVER', 'NATIONAL', 'CONFIDENTIAL',
    'OPERATIONS', 'SUMMARY', 'REPORT', 'APPENDIX', 'SECTION', 'TABLE', 'FIGURE',
    'NOTE', 'CASE', 'CUSTOMER', 'EMPLOYEE', 'SUPPORT', 'PUBLIC',
    'OFFICE', 'PRODUCT', 'SERIAL', 'MODEL', 'FIRMWARE', 'TICKET', 'ACCOUNT', 'INVOICE',
    'ORDER', 'QUANTITY', 'WAREHOUSE', 'AISLE', 'SHELF', 'CREDENTIAL', 'DEVICE',
    'URL', 'HTTP', 'HTTPS', 'WWW', 'ORGANIZATION', 'COMPANY', 'LOCATION', 'NAME',
    'FIRST', 'LAST', 'TITLE', 'STATUS', 'SYSTEM', 'DATA', 'USER', 'PASSWORD',
    'NATIONAL ID', 'DRIVE LICENSE', 'DRIVER LICENSE', 'NATIONAL INSURANCE',
    'CREDIT CARD', 'CARD NUMBER', 'SECURITY', 'AUTHENTICATION', 'EXAMPLE'
}

# Operational metadata prefix patterns (e.g., INV-2026-44081, PROD-2026-77821, ACCT-78451290)
NON_PII_PREFIXES = ('ACCT-', 'INV-', 'PROD-', 'TKT-', 'DEVICE-', 'SESS-', 'WHSEC_', 'SK_TEST_')

class RegexDetector:
    """Detect PII using high-precision regex patterns."""
    
    # Email pattern (RFC compliant)
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # US SSN pattern: XXX-XX-XXXX format strictly
    SSN_PATTERN = r'\b\d{3}-\d{2}-\d{4}\b'
    
    # Aadhaar / National ID pattern: 12 digits formatted as XXXX XXXX XXXX or XXXX-XXXX-XXXX
    AADHAAR_PATTERN = r'\b\d{4}[-\s]\d{4}[-\s]\d{4}\b'

    # PAN Card pattern (India): 5 letters + 4 digits + 1 letter, or synthetic test format PAN-TEST-XXX
    PAN_PATTERN = r'\b(?:PAN-TEST-[A-Z0-9]+|[A-Z]{5}\d{4}[A-Z])\b'

    # Synthetic Government / ID reference patterns (Passport, Tax ID, National Insurance, Driver License)
    GOV_ID_PATTERN = r'\b(?:NI-TEST-[A-Z0-9]+|TAX-TEST-[A-Z0-9]+|TEST-[A-Z0-9-]+|PASSPORT\s+[A-Z0-9]+)\b'
    
    # Credit card: 13 to 16 digits with optional spaces/dashes
    CREDIT_CARD_PATTERN = r'\b(?:\d{4}[\s-]?){3}\d{4}\b'
    
    # Date of birth / Date patterns: DD/MM/YYYY, YYYY-MM-DD, 14 Feb 1991, February 14, 1991
    DOB_PATTERN = r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d{1,2}[-\s](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-\s]\d{4}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b'
    
    # IPv4 address (excluding private 0.x and 255.x)
    IP_PATTERN = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    
    @staticmethod
    def find_emails(text: str) -> List[PIIMatch]:
        """Find email addresses."""
        matches = []
        for match in re.finditer(RegexDetector.EMAIL_PATTERN, text):
            email_str = match.group()
            matches.append(PIIMatch(
                text=email_str,
                pii_type='email',
                start=match.start(),
                end=match.end(),
                confidence=0.95,
                method='regex'
            ))
        return matches
    
    @staticmethod
    def find_phones(text: str) -> List[PIIMatch]:
        """Find phone numbers (US, UK, Indian, International)."""
        matches = []
        patterns = [
            r'\+(?:[0-9][\s.-]?){7,14}[0-9]\b',  # +91 91234 56789, +44 7700 900123, +1 202-555-0199
            r'\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b',  # (415) 555-0138, 202-555-0199, 212-555-0144
            r'\b[6-9]\d{4}[\s.-]?\d{5}\b',  # Indian 10-digit format starting with 6-9
        ]
        combined_pattern = '|'.join(f'(?:{p})' for p in patterns)
        for match in re.finditer(combined_pattern, text):
            matched_text = match.group().strip()
            digits_only = re.sub(r'\D', '', matched_text)
            # Ensure proper length and avoid matching pure credit cards (16 digits) or SSNs
            if 7 <= len(digits_only) <= 15 and not RegexDetector._luhn_check(digits_only):
                matches.append(PIIMatch(
                    text=matched_text,
                    pii_type='phone',
                    start=match.start(),
                    end=match.end(),
                    confidence=0.85,
                    method='regex'
                ))
        return matches
    
    @staticmethod
    def find_ssns(text: str) -> List[PIIMatch]:
        """Find US SSNs."""
        matches = []
        for match in re.finditer(RegexDetector.SSN_PATTERN, text):
            matched_text = match.group()
            matches.append(PIIMatch(
                text=matched_text,
                pii_type='ssn',
                start=match.start(),
                end=match.end(),
                confidence=0.90,
                method='regex'
            ))
        return matches

    @staticmethod
    def find_aadhaar_and_gov_ids(text: str) -> List[PIIMatch]:
        """Find Aadhaar numbers, PAN cards, and government ID references."""
        matches = []
        # Aadhaar
        for match in re.finditer(RegexDetector.AADHAAR_PATTERN, text):
            matches.append(PIIMatch(
                text=match.group(),
                pii_type='ssn',
                start=match.start(),
                end=match.end(),
                confidence=0.85,
                method='regex'
            ))
        # PAN Cards
        for match in re.finditer(RegexDetector.PAN_PATTERN, text):
            matches.append(PIIMatch(
                text=match.group(),
                pii_type='ssn',
                start=match.start(),
                end=match.end(),
                confidence=0.90,
                method='regex'
            ))
        # Other synthetic Gov IDs
        for match in re.finditer(RegexDetector.GOV_ID_PATTERN, text):
            matches.append(PIIMatch(
                text=match.group(),
                pii_type='ssn',
                start=match.start(),
                end=match.end(),
                confidence=0.85,
                method='regex'
            ))
        return matches
    
    @staticmethod
    def find_credit_cards(text: str) -> List[PIIMatch]:
        """Find credit card numbers with Luhn check validation."""
        matches = []
        for match in re.finditer(RegexDetector.CREDIT_CARD_PATTERN, text):
            matched_text = match.group()
            digits_only = re.sub(r'\D', '', matched_text)
            if len(digits_only) == 16 and RegexDetector._luhn_check(digits_only):
                matches.append(PIIMatch(
                    text=matched_text,
                    pii_type='credit_card',
                    start=match.start(),
                    end=match.end(),
                    confidence=0.92,
                    method='regex'
                ))
        return matches
    
    @staticmethod
    def find_dobs(text: str) -> List[PIIMatch]:
        """Find dates of birth / dates."""
        matches = []
        for match in re.finditer(RegexDetector.DOB_PATTERN, text):
            matches.append(PIIMatch(
                text=match.group(),
                pii_type='dob',
                start=match.start(),
                end=match.end(),
                confidence=0.75,
                method='regex'
            ))
        return matches
    
    @staticmethod
    def find_ips(text: str) -> List[PIIMatch]:
        """Find IPv4 addresses."""
        matches = []
        for match in re.finditer(RegexDetector.IP_PATTERN, text):
            matched_text = match.group()
            if not matched_text.startswith(('0.', '255.')):
                matches.append(PIIMatch(
                    text=matched_text,
                    pii_type='ip',
                    start=match.start(),
                    end=match.end(),
                    confidence=0.88,
                    method='regex'
                ))
        return matches
    
    @staticmethod
    def _luhn_check(card_number: str) -> bool:
        """Validate credit card using Luhn algorithm."""
        if not card_number.isdigit() or len(card_number) < 13:
            return False
        digits = [int(d) for d in card_number]
        digits.reverse()
        total = 0
        for i, d in enumerate(digits):
            if i % 2 == 1:
                d *= 2
                if d > 9:
                    d -= 9
            total += d
        return total % 10 == 0

class NERDetector:
    """Detect PII using spaCy NER with filtering."""
    
    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')
    
    def _is_valid_entity(self, text: str) -> bool:
        """Filter out non-PII words, operational ref IDs, and formatting artifacts."""
        clean_text = text.strip(" \t\n\r.,;:()[]{}'\"")
        if not clean_text or len(clean_text) < 2:
            return False
        
        upper_text = clean_text.upper()
        if upper_text in NON_PII_WORDS:
            return False
        
        # Check non-PII prefixes (e.g. ACCT-..., INV-..., PROD-...)
        for prefix in NON_PII_PREFIXES:
            if upper_text.startswith(prefix):
                return False
        
        # Exclude monetary amounts (e.g. INR 18,450.00, USD 742.18)
        if re.match(r'^(?:INR|USD|EUR|GBP|CAD|AUD|\$|₹|£|€)\s*[\d,]+(?:\.\d+)?$', clean_text, re.I):
            return False

        # Exclude pure digits or numbers
        if clean_text.isdigit():
            return False

        return True

    def find_names(self, text: str) -> List[PIIMatch]:
        """Find person names using NER."""
        doc = self.nlp(text)
        matches = []
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                clean_text = ent.text.strip(" \t\n\r.,;:()[]{}'\"")
                if self._is_valid_entity(clean_text):
                    matches.append(PIIMatch(
                        text=clean_text,
                        pii_type='name',
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=0.82,
                        method='ner'
                    ))
        return matches
    
    def find_organizations(self, text: str) -> List[PIIMatch]:
        """Find organization names using NER."""
        doc = self.nlp(text)
        matches = []
        for ent in doc.ents:
            if ent.label_ == 'ORG':
                clean_text = ent.text.strip(" \t\n\r.,;:()[]{}'\"")
                if self._is_valid_entity(clean_text):
                    matches.append(PIIMatch(
                        text=clean_text,
                        pii_type='company',
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=0.78,
                        method='ner'
                    ))
        return matches
    
    def find_locations(self, text: str) -> List[PIIMatch]:
        """Find locations (cities, states, countries, addresses) using NER."""
        doc = self.nlp(text)
        matches = []
        for ent in doc.ents:
            if ent.label_ in ('GPE', 'LOC', 'FAC'):
                clean_text = ent.text.strip(" \t\n\r.,;:()[]{}'\"")
                if self._is_valid_entity(clean_text):
                    matches.append(PIIMatch(
                        text=clean_text,
                        pii_type='location',
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=0.75,
                        method='ner'
                    ))
        return matches

class HybridPIIDetector:
    """Combined regex + NER detector with deduplication and accuracy tuning."""
    
    def __init__(self):
        self.regex_detector = RegexDetector()
        self.ner_detector = NERDetector()
    
    def detect_all(self, text: str, min_confidence: float = 0.65) -> List[PIIMatch]:
        """Detect all PII types and deduplicate overlapping matches."""
        matches = []
        
        # Regex detections (highest specificity first)
        matches.extend(self.regex_detector.find_emails(text))
        matches.extend(self.regex_detector.find_phones(text))
        matches.extend(self.regex_detector.find_ssns(text))
        matches.extend(self.regex_detector.find_aadhaar_and_gov_ids(text))
        matches.extend(self.regex_detector.find_credit_cards(text))
        matches.extend(self.regex_detector.find_dobs(text))
        matches.extend(self.regex_detector.find_ips(text))
        
        # NER detections
        matches.extend(self.ner_detector.find_names(text))
        matches.extend(self.ner_detector.find_organizations(text))
        matches.extend(self.ner_detector.find_locations(text))
        
        # Clean entity text and filter out invalid / blocked terms
        cleaned_matches = []
        for m in matches:
            clean_str = m.text.strip(" \t\n\r.,;:()[]{}'\"")
            if clean_str and m.confidence >= min_confidence:
                upper = clean_str.upper()
                if upper not in NON_PII_WORDS and not any(upper.startswith(p) for p in NON_PII_PREFIXES):
                    m.text = clean_str
                    cleaned_matches.append(m)
        
        # Deduplicate overlapping matches (keep highest confidence match)
        deduped = self._deduplicate(cleaned_matches)
        
        # Sort by position
        deduped.sort(key=lambda m: m.start)
        
        return deduped
    
    @staticmethod
    def _deduplicate(matches: List[PIIMatch]) -> List[PIIMatch]:
        """Remove duplicate/overlapping matches, keeping highest confidence."""
        if not matches:
            return []
        
        # Sort by start position, then by confidence (descending), then by length (descending)
        sorted_matches = sorted(matches, key=lambda m: (m.start, -m.confidence, -len(m.text)))
        
        deduplicated = []
        for match in sorted_matches:
            overlaps = False
            for existing in deduplicated:
                if not (match.end <= existing.start or match.start >= existing.end):
                    overlaps = True
                    break
            
            if not overlaps:
                deduplicated.append(match)
        
        return deduplicated
