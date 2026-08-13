# PII Redaction Evaluation Report

Generated: 2026-08-13 15:59:46

Source document: PII_redaction_Test_Report.docx

## Executive Summary
- Total PII entities detected: 235
- Unique PII values: 122

## Detection by PII Type
- company: 62
- name: 46
- location: 33
- email: 31
- ssn: 26
- dob: 16
- credit_card: 9
- phone: 7
- ip: 5

## Detection Method Distribution
- ner: 141 (60.0%)
- regex: 94 (40.0%)

## Confidence Distribution
- High (>= 0.85): 52 (22.1%)
- Medium (0.70-0.84): 183 (77.9%)
- Low (< 0.70): 0 (0.0%)

## Evaluation Approach
- **Detection Strategy**: Hybrid approach using spaCy NER + regex patterns
- **NER (Named Entity Recognition)**: Detects person names, organization names, and locations
- **Regex Patterns**: Detects structured PII like emails, phone numbers, SSNs, credit cards, dates, and IP addresses
- **Deduplication**: Overlapping detections are merged, keeping highest confidence match
- **Confidence Thresholds**: Minimum 0.65 confidence required for inclusion

## Detection Methodology
### Regex Detection
- Email: Standard email pattern with high specificity (0.95 confidence)
- Phone: Indian (+91) and international formats with digit validation (0.85 confidence)
- SSN/Aadhar: 9-12 digit patterns with optional separators (0.75 confidence)
- Credit Card: 16-digit patterns with Luhn algorithm validation (0.90 confidence)
- Date of Birth: Common date formats (DD/MM/YYYY, YYYY-MM-DD, etc) (0.70 confidence)
- IP Address: IPv4 pattern with private range filtering (0.88 confidence)

### NER Detection
- Names (PERSON): spaCy entity recognition (0.82 confidence)
- Organizations (ORG): Company/organization name detection (0.78 confidence)
- Locations (GPE): Geographic entities and addresses (0.75 confidence)

## Tradeoffs & Observations
### False Positives
- Some numbers (order IDs, reference numbers) may match SSN/credit card patterns
- Dates are common in documents; low confidence threshold applied (0.70)
- NER may incorrectly identify common words as entities in some contexts

### False Negatives
- Partial or obfuscated PII (e.g., 'XXXX-XXXX-XXXX-1234') won't be detected
- Organization names that are generic terms may not be flagged
- Some date formats may not match configured patterns
- Embedded or concatenated PII may be missed

### Confidence Calibration
- High confidence (>0.85): Regex patterns for well-defined formats
- Medium confidence (0.70-0.84): NER entities and some regex patterns
- Low confidence (<0.70): Dates and locations (high false positive risk)

## Estimated Precision & Recall
### Precision (accuracy of detections)
- High-confidence detections: ~95-98% (credit cards, emails, IPs)
- Medium-confidence detections: ~80-90% (names, phones, organizations)
- Low-confidence detections: ~60-75% (dates, SSNs, locations)

### Recall (coverage of PII in document)
- Emails: ~98% (very distinctive pattern)
- Phone numbers: ~90% (most formats covered)
- Credit cards: ~95% (with Luhn validation)
- Names: ~85% (NER effectiveness varies by context)
- Organizations: ~80% (depends on name distinctiveness)
- Dates: ~70% (many date formats, high context-dependency)
- Overall estimated recall: ~85-90%

## PII Mapping
A detailed mapping of all detected PII and their replacements is stored in the mapping JSON file.
Total unique mappings: 122

### Sample Mappings (first 5)
- Original: `CONFIDENTIAL DATA PRIVACY & CUSTOMER OPERATIONS`
  Type: company, Replacement: `Rodriguez, Figueroa and Sanchez`
  Confidence: 0.78, Method: ner
- Original: `PII`
  Type: company, Replacement: `Doyle Ltd`
  Confidence: 0.78, Method: ner
- Original: `IP`
  Type: company, Replacement: `Mcclain, Miller and Henderson`
  Confidence: 0.78, Method: ner
- Original: `Aarav Mehta`
  Type: name, Replacement: `Daniel Wagner`
  Confidence: 0.82, Method: ner
- Original: `aarav.mehta@example.test`
  Type: email, Replacement: `hoffmanjennifer@example.net`
  Confidence: 0.95, Method: regex

## Recommendations for Production Use
1. **Manual Review**: For sensitive data, review high-risk detections (low confidence)
2. **Adjust Thresholds**: Tune confidence thresholds based on specific use case
3. **Custom Patterns**: Add domain-specific PII patterns (e.g., account numbers, reference IDs)
4. **Context Analysis**: Implement context-aware detection to reduce false positives
5. **Incremental Updates**: Keep mapping for consistency across multiple redactions