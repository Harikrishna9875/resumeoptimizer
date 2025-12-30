import fitz  # PyMuPDF
import re

def pdf_to_latex(pdf_path):
    """Convert PDF resume to LaTeX format"""
    doc = fitz.open(pdf_path)
    full_text = ""
    
    for page in doc:
        full_text += page.get_text()
    
    doc.close()
    
    # Parse sections
    name = extract_name(full_text)
    email = extract_email(full_text)
    phone = extract_phone(full_text)
    education = extract_section(full_text, "EDUCATION")
    experience = extract_section(full_text, "EXPERIENCE")
    skills = extract_section(full_text, "SKILLS")
    
    # Generate LaTeX
    latex = f"""\\documentclass[a4paper,11pt]{{article}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage{{enumitem}}

\\begin{{document}}

\\begin{{center}}
  {{\\Large \\textbf{{{name}}}}}\\\\
  {email} | {phone}
\\end{{center}}

\\section*{{Education}}
{education}

\\section*{{Skills}}
{skills}

\\section*{{Experience}}
{experience}

\\end{{document}}"""
    
    return latex

def extract_name(text):
    lines = text.split('\n')
    return lines[0].strip() if lines else "Your Name"

def extract_email(text):
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else "email@example.com"

def extract_phone(text):
    match = re.search(r'[\+\d][\d\-\.\s\(\)]{8,}[\d]', text)
    return match.group(0).strip() if match else "555-0123"

def extract_section(text, section_name):
    """Extract content between section headers"""
    pattern = rf'{section_name}(.*?)(?=[A-Z]{{3,}}|\Z)'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    
    if match:
        content = match.group(1).strip()
        # Convert to LaTeX bullet points
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        return '\n'.join([f'- {line}' if not line.startswith('-') else line for line in lines[:5]])
    
    return "Add your " + section_name.lower() + " here"
