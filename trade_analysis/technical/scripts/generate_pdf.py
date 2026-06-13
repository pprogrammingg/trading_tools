#!/usr/bin/env python3
"""
Script to convert DOCUMENTATION.md to PDF
Tries multiple methods in order of preference.
"""

import subprocess
import sys
import os

def try_wkhtmltopdf():
    """Try using wkhtmltopdf (best quality)"""
    html_file = 'DOCUMENTATION.html'
    pdf_file = 'DOCUMENTATION.pdf'
    
    if not os.path.exists(html_file):
        print("Error: DOCUMENTATION.html not found")
        return False
    
    try:
        result = subprocess.run(
            ['wkhtmltopdf', '--page-size', 'A4', '--margin-top', '20mm', 
             '--margin-bottom', '20mm', '--margin-left', '20mm', 
             '--margin-right', '20mm', html_file, pdf_file],
            capture_output=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"✓ PDF generated: {pdf_file}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return False

def try_macos_print():
    """Try using macOS print to PDF"""
    html_file = 'DOCUMENTATION.html'
    pdf_file = 'DOCUMENTATION.pdf'
    
    if not os.path.exists(html_file):
        return False
    
    # On macOS, can use open command to print to PDF
    # But this requires user interaction, so we'll just note it
    if sys.platform == 'darwin':
        print("  Note: On macOS, you can convert HTML to PDF by:")
        print(f"        open {html_file}")
        print("        Then use File > Export as PDF")
    return False

def try_weasyprint():
    """Try using weasyprint"""
    html_file = 'DOCUMENTATION.html'
    pdf_file = 'DOCUMENTATION.pdf'
    
    try:
        from weasyprint import HTML
        HTML(html_file).write_pdf(pdf_file)
        print(f"✓ PDF generated: {pdf_file}")
        return True
    except ImportError:
        print("  weasyprint not installed (pip install weasyprint)")
    except Exception as e:
        print(f"  weasyprint error: {e}")
    return False

def try_pdfkit():
    """Try using pdfkit (requires wkhtmltopdf)"""
    html_file = 'DOCUMENTATION.html'
    pdf_file = 'DOCUMENTATION.pdf'
    
    try:
        import pdfkit
        options = {
            'page-size': 'A4',
            'margin-top': '20mm',
            'margin-bottom': '20mm',
            'margin-left': '20mm',
            'margin-right': '20mm',
        }
        pdfkit.from_file(html_file, pdf_file, options=options)
        print(f"✓ PDF generated: {pdf_file}")
        return True
    except ImportError:
        print("  pdfkit not installed (pip install pdfkit)")
    except Exception as e:
        print(f"  pdfkit error: {e}")
    return False

def main():
    print("Converting DOCUMENTATION.md to PDF...\n")
    
    # Try methods in order
    if try_wkhtmltopdf():
        return 0
    
    if try_weasyprint():
        return 0
    
    if try_pdfkit():
        return 0
    
    print("\n⚠ No PDF converter available.")
    print("\nTo generate PDF, install one of:")
    print("  1. wkhtmltopdf: brew install wkhtmltopdf")
    print("  2. weasyprint: pip install weasyprint")
    print("  3. pdfkit: pip install pdfkit (requires wkhtmltopdf)")
    print("\nHTML version available: DOCUMENTATION.html")
    return 1

if __name__ == '__main__':
    sys.exit(main())
