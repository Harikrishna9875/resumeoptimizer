import fitz  # PyMuPDF
import re

def pdf_to_latex(pdf_path):
    """Convert PDF resume to LaTeX format"""
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        
        for page in doc:
            full_text += page.get_text()
        
        doc.close()
        
        # Extract information
        name = extract_name(full_text)
        contact = extract_contact(full_text)
        education = extract_section_content(full_text, ["EDUCATION", "ACADEMIC"])
        skills = extract_section_content(full_text, ["SKILLS", "TECHNICAL SKILLS"])
        experience = extract_section_content(full_text, ["EXPERIENCE", "WORK EXPERIENCE"])
        
        # Generate LaTeX
        latex = f"""\\documentclass[a4paper,11pt]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[margin=0.8in]{{geometry}}
\\usepackage{{enumitem}}

\\begin{{document}}

\\begin{{center}}
  {{\\Large \\textbf{{{name}}}}}\\\\
  {contact}
\\end{{center}}

\\section*{{Education}}
{education or "BS Computer Science, University Name, 2023"}

\\section*{{Skills}}
{skills or "Python, JavaScript, React, Node.js, SQL, Git"}

\\section*{{Experience}}
{experience or "Software Developer Intern, Company Name - 2023\\n- Built web applications"}

\\end{{document}}"""
        
        return latex
        
    except Exception as e:
        # Return default template if parsing fails
        return """\\documentclass[a4paper,11pt]{article}
\\usepackage[margin=1in]{geometry}

\\begin{document}

\\begin{center}
  {\\Large \\textbf{Your Name}}\\\\
  email@example.com | 555-0123
\\end{center}

\\section*{Education}
BS Computer Science, University Name, 2023

\\section*{Skills}
Python, JavaScript, React, Django, SQL

\\section*{Experience}
Software Developer Intern - Summer 2023
- Built web applications
- Worked with databases

\\end{document}"""

def extract_name(text):
    """Extract name from first few lines"""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    for line in lines[:3]:
        if len(line.split()) <= 4 and not '@' in line and not re.search(r'\d{3}', line):
            return line.title()
    return "Your Name"

def extract_contact(text):
    """Extract email and phone"""
    email = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    phone = re.search(r'[\+\d][\d\-\.\s\(\)]{8,}', text)
    
    parts = []
    if email:
        parts.append(email.group(0))
    if phone:
        parts.append(phone.group(0).strip())
    
    return ' | '.join(parts) if parts else 'email@example.com | 555-0123'

def extract_section_content(text, keywords):
    """Extract content from section"""
    text_upper = text.upper()
    for keyword in keywords:
        pos = text_upper.find(keyword)
        if pos != -1:
            # Get content after section header
            after_section = text[pos + len(keyword):pos + len(keyword) + 500]
            lines = [l.strip() for l in after_section.split('\n') if l.strip()]
            if lines:
                return '\n'.join([f'- {l}' if not l.startswith('-') else l for l in lines[:5]])
    return ""
