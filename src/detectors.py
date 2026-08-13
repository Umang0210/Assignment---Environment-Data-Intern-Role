import re
import spacy
from typing import List, Tuple, Dict
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

class RegexDetector:
    """Detect PII using regex patterns."""
    
    # Email pattern
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Phone patterns: +91 XXXXXXXXXX, +XX XXXXXXXXX, or plain digits
    PHONE_PATTERN = r'(?:\+91[\s]?)?[6-9]\d{9}\b|(?:\+\d{1,3}[\s]?\d{1,14})\b'
    
    # SSN/Aadhar: 9-12 digits possibly with spaces/dashes
    SSN_PATTERN = r'\b\d{3}[-\s]?\d{2,3}[-\s]?\d{4,5}\b'
    
    # Credit card: 16 digits with optional spaces/dashes
    CREDIT_CARD_PATTERN = r'\b(?:\d{4}[\s-]?){3}\d{4}\b'
    
    # Date of birth: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, YYYY/MM/DD
    DOB_PATTERN = r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b'
    
    # IPv4 address
    IP_PATTERN = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    
    @staticmethod
    def find_emails(text: str) -> List[PIIMatch]:
        """Find email addresses."""
        matches = []
        for match in re.finditer(RegexDetector.EMAIL_PATTERN, text):
            matches.append(PIIMatch(
                text=match.group(),
                pii_type='email',
                start=match.start(),
                end=match.end(),
                confidence=0.95,
                method='regex'
            ))
        return matches
    
    @staticmethod
    def find_phones(text: str) -> List[PIIMatch]:
        """Find phone numbers."""
        matches = []
        for match in re.finditer(RegexDetector.PHONE_PATTERN, text):
            # filter false positives: plain 10-digit numbers that don't look like phones
            matched_text = match.group().strip()
            if len(matched_text) >= 10 and ('+' in matched_text or matched_text[0] in '6789'):
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
        """Find SSN/Aadhar numbers."""
        matches = []
        for match in re.finditer(RegexDetector.SSN_PATTERN, text):
            matched_text = match.group()
            # validate: should have enough digits (9-12)
            digit_count = len(matched_text.replace('-', '').replace(' ', ''))
            if 9 <= digit_count <= 12:
                matches.append(PIIMatch(
                    text=matched_text,
                    pii_type='ssn',
                    start=match.start(),
                    end=match.end(),
                    confidence=0.75,  # lower confidence due to false positives
                    method='regex'
                ))
        return matches
    
    @staticmethod
    def find_credit_cards(text: str) -> List[PIIMatch]:
        """Find credit card numbers."""
        matches = []
        for match in re.finditer(RegexDetector.CREDIT_CARD_PATTERN, text):
            matched_text = match.group()
            # validate luhn for actual card numbers
            digits_only = matched_text.replace(' ', '').replace('-', '')
            if RegexDetector._luhn_check(digits_only):
                matches.append(PIIMatch(
                    text=matched_text,
                    pii_type='credit_card',
                    start=match.start(),
                    end=match.end(),
                    confidence=0.9,
                    method='regex'
                ))
        return matches
    
    @staticmethod
    def find_dobs(text: str) -> List[PIIMatch]:
        """Find dates of birth."""
        matches = []
        for match in re.finditer(RegexDetector.DOB_PATTERN, text):
            matches.append(PIIMatch(
                text=match.group(),
                pii_type='dob',
                start=match.start(),
                end=match.end(),
                confidence=0.7,  # lower confidence: dates are common
                method='regex'
            ))
        return matches
    
    @staticmethod
    def find_ips(text: str) -> List[PIIMatch]:
        """Find IP addresses."""
        matches = []
        for match in re.finditer(RegexDetector.IP_PATTERN, text):
            matched_text = match.group()
            # filter private/reserved ranges if needed
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
    """Detect PII using spaCy NER."""
    
    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')
    
    def find_names(self, text: str) -> List[PIIMatch]:
        """Find person names using NER."""
        doc = self.nlp(text)
        matches = []
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                matches.append(PIIMatch(
                    text=ent.text,
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
                matches.append(PIIMatch(
                    text=ent.text,
                    pii_type='company',
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=0.78,
                    method='ner'
                ))
        return matches
    
    def find_locations(self, text: str) -> List[PIIMatch]:
        """Find locations (potential addresses) using NER."""
        doc = self.nlp(text)
        matches = []
        for ent in doc.ents:
            if ent.label_ == 'GPE':  # geopolitical entity
                matches.append(PIIMatch(
                    text=ent.text,
                    pii_type='location',
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=0.75,
                    method='ner'
                ))
        return matches

class HybridPIIDetector:
    """Combined regex + NER detector with deduplication."""
    
    def __init__(self):
        self.regex_detector = RegexDetector()
        self.ner_detector = NERDetector()
    
    def detect_all(self, text: str, min_confidence: float = 0.65) -> List[PIIMatch]:
        """Detect all PII types and deduplicate overlapping matches."""
        matches = []
        
        # Regex detections
        matches.extend(self.regex_detector.find_emails(text))
        matches.extend(self.regex_detector.find_phones(text))
        matches.extend(self.regex_detector.find_ssns(text))
        matches.extend(self.regex_detector.find_credit_cards(text))
        matches.extend(self.regex_detector.find_dobs(text))
        matches.extend(self.regex_detector.find_ips(text))
        
        # NER detections
        matches.extend(self.ner_detector.find_names(text))
        matches.extend(self.ner_detector.find_organizations(text))
        matches.extend(self.ner_detector.find_locations(text))
        
        # Filter by confidence
        matches = [m for m in matches if m.confidence >= min_confidence]
        
        # Deduplicate overlapping matches (keep highest confidence)
        matches = self._deduplicate(matches)
        
        # Sort by position
        matches.sort(key=lambda m: m.start)
        
        return matches
    
    @staticmethod
    def _deduplicate(matches: List[PIIMatch]) -> List[PIIMatch]:
        """Remove duplicate/overlapping matches, keeping highest confidence."""
        if not matches:
            return []
        
        # Sort by start position, then by confidence (descending)
        sorted_matches = sorted(matches, key=lambda m: (m.start, -m.confidence))
        
        deduplicated = []
        for match in sorted_matches:
            # Check if this match overlaps with any already added
            overlaps = False
            for existing in deduplicated:
                if not (match.end <= existing.start or match.start >= existing.end):
                    overlaps = True
                    break
            
            if not overlaps:
                deduplicated.append(match)
        
        return deduplicated
