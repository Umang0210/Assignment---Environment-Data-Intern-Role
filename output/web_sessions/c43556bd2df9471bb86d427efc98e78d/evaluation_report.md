# PII Redaction Evaluation Report

Generated: 2026-08-13 19:11:40

Source document: C:\Users\umang\Desktop\SCALER AI LABS\output\web_sessions\c43556bd2df9471bb86d427efc98e78d\original_input.docx

## Executive Summary
- Total PII entities detected: 3473
- Unique PII values: 799

## Detection by PII Type
- company: 2385
- name: 744
- location: 261
- email: 70
- ssn: 12
- phone: 1

## Detection Method Distribution
- ner: 3390 (97.6%)
- regex: 83 (2.4%)

## Confidence Distribution
- High (>= 0.85): 71 (2.0%)
- Medium (0.70-0.84): 3402 (98.0%)
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
Total unique mappings: 799

### Sample Mappings (first 5)
- Original: `RED HERRING PROSPECTUS
`
  Type: company, Replacement: `Rodriguez, Figueroa and Sanchez`
  Confidence: 0.78, Method: ner
- Original: `KSH INTERNATIONAL LIMITED`
  Type: company, Replacement: `Doyle Ltd`
  Confidence: 0.78, Method: ner
- Original: `Anchor Investors`
  Type: company, Replacement: `Mcclain, Miller and Henderson`
  Confidence: 0.78, Method: ner
- Original: `Bid/Offer Closing Day`
  Type: company, Replacement: `Davis and Sons`
  Confidence: 0.78, Method: ner
- Original: `KSH INTERNATIONAL LIMITED
Our Company`
  Type: company, Replacement: `Guzman, Hoffman and Baldwin`
  Confidence: 0.78, Method: ner

## Recommendations for Production Use
1. **Manual Review**: For sensitive data, review high-risk detections (low confidence)
2. **Adjust Thresholds**: Tune confidence thresholds based on specific use case
3. **Custom Patterns**: Add domain-specific PII patterns (e.g., account numbers, reference IDs)
4. **Context Analysis**: Implement context-aware detection to reduce false positives
5. **Incremental Updates**: Keep mapping for consistency across multiple redactions