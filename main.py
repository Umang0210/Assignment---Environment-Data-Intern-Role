#!/usr/bin/env python3
"""
PII Redaction Tool
Detects and redacts personally identifiable information from documents.
Uses hybrid approach: spaCy NER + regex patterns.
"""

import argparse
import sys
import os
from pathlib import Path
from src.redactor import PIIRedactor
from src.faker_provider import FakeDataGenerator

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(
        description='Redact personally identifiable information from Word documents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py input.docx
  python main.py input.docx -o output.docx -m mapping.json -r report.md
  python main.py input.docx --confidence 0.70
        """
    )
    
    parser.add_argument('input', help='Input Word document (.docx)')
    parser.add_argument('-o', '--output', default='output/redacted_document.docx',
                       help='Output redacted document (default: output/redacted_document.docx)')
    parser.add_argument('-c', '--copy', default='output/original_document.docx',
                       help='Save copy of original document (default: output/original_document.docx)')
    parser.add_argument('-m', '--mapping', default='output/pii_mapping.json',
                       help='Save PII mapping to JSON file (default: output/pii_mapping.json)')
    parser.add_argument('-r', '--report', default='evaluation/evaluation_report.md',
                       help='Save evaluation report (default: evaluation/evaluation_report.md)')
    parser.add_argument('--confidence', type=float, default=0.65,
                       help='Minimum confidence threshold for PII detection (default: 0.65)')
    parser.add_argument('--reset-cache', action='store_true',
                       help='Reset fake data generator cache (for fresh runs)')
    
    args = parser.parse_args()
    
    # Validate input
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        sys.exit(1)
    
    if not args.input.lower().endswith('.docx'):
        print("Error: Input must be a .docx file", file=sys.stderr)
        sys.exit(1)
    
    if not 0.0 <= args.confidence <= 1.0:
        print("Error: Confidence must be between 0.0 and 1.0", file=sys.stderr)
        sys.exit(1)
    
    # Reset cache if requested
    if args.reset_cache:
        FakeDataGenerator.reset_cache()
    
    print(f"🔍 PII Redaction Tool")
    print(f"Input: {args.input}")
    print(f"Confidence threshold: {args.confidence}")
    print()
    
    try:
        # Create redactor
        print("📄 Loading document...")
        redactor = PIIRedactor(args.input)
        
        # Execute redaction
        print("🔎 Detecting PII...")
        num_replacements, stats = redactor.redact(min_confidence=args.confidence)
        
        # Save outputs
        print(f"💾 Saving redacted document...")
        redactor.save_redacted(args.output)
        
        print(f"💾 Saving original copy...")
        redactor.save_original_copy(args.copy)
        
        print(f"💾 Saving PII mapping...")
        redactor.save_mapping(args.mapping)
        
        print(f"📊 Generating evaluation report...")
        redactor.generate_evaluation_report(args.report, stats)
        
        # Print summary
        print()
        print("✅ Redaction Complete!")
        print()
        print("📊 Summary:")
        print(f"  Total PII detected: {stats['total_pii_detected']}")
        print(f"  Unique PII values: {stats['total_unique_pii']}")
        print()
        print("  By type:")
        for pii_type, count in sorted(stats['by_type'].items(), key=lambda x: x[1], reverse=True):
            print(f"    - {pii_type}: {count}")
        print()
        print("  By confidence:")
        print(f"    - High (>= 0.85): {stats['by_confidence']['high']}")
        print(f"    - Medium (0.70-0.84): {stats['by_confidence']['medium']}")
        print(f"    - Low (< 0.70): {stats['by_confidence']['low']}")
        print()
        print("📁 Output files:")
        print(f"  - Redacted: {args.output}")
        print(f"  - Original copy: {args.copy}")
        print(f"  - PII Mapping: {args.mapping}")
        print(f"  - Evaluation report: {args.report}")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
