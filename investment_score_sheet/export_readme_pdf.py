#!/usr/bin/env python3
"""
Export README.md to PDF format
"""
import markdown
from weasyprint import HTML, CSS
from pathlib import Path

def convert_readme_to_pdf():
    # Look for README in parent directory
    readme_path = Path('../README.md')
    if not readme_path.exists():
        readme_path = Path('README.md')
    pdf_path = Path('../README.pdf')
    if not pdf_path.parent.exists():
        pdf_path = Path('README.pdf')
    
    if not readme_path.exists():
        print(f"Error: {readme_path} not found!")
        return False
    
    # Read markdown
    with open(readme_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Convert markdown to HTML
    html_content = markdown.markdown(markdown_content, extensions=['extra', 'codehilite'])
    
    # Add CSS styling
    styled_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: letter;
                margin: 0.75in;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                max-width: 100%;
                margin: 0;
                padding: 0;
                color: #333;
                font-size: 11pt;
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                font-size: 24pt;
                margin-top: 0;
                page-break-after: avoid;
            }}
            h2 {{
                color: #34495e;
                border-bottom: 2px solid #ecf0f1;
                padding-bottom: 5px;
                margin-top: 20px;
                font-size: 18pt;
                page-break-after: avoid;
            }}
            h3 {{
                color: #7f8c8d;
                margin-top: 15px;
                font-size: 14pt;
                page-break-after: avoid;
            }}
            h4 {{
                font-size: 12pt;
                margin-top: 12px;
                page-break-after: avoid;
            }}
            code {{
                background-color: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
            }}
            pre {{
                background-color: #f4f4f4;
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
                border-left: 4px solid #3498db;
                font-size: 9pt;
                page-break-inside: avoid;
            }}
            ul, ol {{
                margin-left: 20px;
                margin-top: 8px;
                margin-bottom: 8px;
            }}
            li {{
                margin: 4px 0;
            }}
            p {{
                margin: 8px 0;
            }}
            strong {{
                color: #2c3e50;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 15px 0;
                font-size: 9pt;
                page-break-inside: avoid;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 6px;
                text-align: left;
            }}
            th {{
                background-color: #3498db;
                color: white;
            }}
            /* Ensure content fits on page */
            * {{
                box-sizing: border-box;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Convert HTML to PDF
    try:
        HTML(string=styled_html).write_pdf(pdf_path)
        print(f"✓ PDF created: {pdf_path}")
        print(f"  File size: {pdf_path.stat().st_size / 1024:.1f} KB")
        return True
    except Exception as e:
        print(f"Error creating PDF: {e}")
        return False

if __name__ == "__main__":
    convert_readme_to_pdf()
