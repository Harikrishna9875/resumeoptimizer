import os
import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .pdf_parser import pdf_to_latex
from django.conf import settings

def index(request):
    return render(request, 'index.html')

@csrf_exempt
@require_http_methods(["POST"])
def upload_pdf(request):
    """Convert uploaded PDF to LaTeX"""
    try:
        if 'pdf_file' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No PDF file uploaded'}, status=400)
        
        pdf_file = request.FILES['pdf_file']
        if not pdf_file.name.lower().endswith('.pdf'):
            return JsonResponse({'success': False, 'error': 'Please upload a PDF file'}, status=400)
        
        # Save temporarily
        temp_path = f'temp/{pdf_file.name}'
        file_path = default_storage.save(temp_path, ContentFile(pdf_file.read()))
        full_path = default_storage.path(file_path)
        
        # Convert to LaTeX
        latex_code = pdf_to_latex(full_path)
        
        # Cleanup
        default_storage.delete(file_path)
        
        return JsonResponse({
            'success': True,
            'latex_code': latex_code,
            'message': 'PDF converted to LaTeX successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'PDF conversion failed: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def optimize_resume(request):
    try:
        data = json.loads(request.body)
        latex_code = data.get('latex_code', '').strip()
        job_description = data.get('job_description', '').strip()

        if not latex_code or not job_description:
            return JsonResponse({'success': False, 'error': 'Both LaTeX resume and job description required'}, status=400)

        # Use GROQ API
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            return JsonResponse({'success': False, 'error': 'API key not configured'}, status=500)

        url = "https://api.groq.com/openai/v1/chat/completions"
        
        prompt = f"""You are an expert ATS resume optimizer. Analyze the job description and enhance the LaTeX resume.

JOB DESCRIPTION:
{job_description}

RESUME TO OPTIMIZE:
{latex_code}

TASKS:
1. Add exact keywords from job description naturally into bullet points
2. Keep ALL LaTeX structure perfect (commands, braces, sections)
3. Maintain original formatting and layout
4. Return 3-5 actionable improvement suggestions

OUTPUT ONLY VALID JSON (no markdown):
{{
  "keywords_added": ["Django", "PostgreSQL", "REST API"],
  "modified_latex": "COMPLETE LaTeX code with \\\\textbf, \\\\section etc",
  "match_score": 87,
  "suggestions": ["Quantify achievements with numbers", "Add more action verbs", "Include GitHub link"]
}}

CRITICAL: Use double backslashes \\\\ for ALL LaTeX commands."""

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are an ATS resume expert. ALWAYS return clean JSON with properly escaped LaTeX (double backslashes). Never use markdown code blocks."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 8000
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            error_msg = response.json().get('error', {}).get('message', 'Groq API error')
            return JsonResponse({'success': False, 'error': error_msg}, status=500)
        
        response_data = response.json()
        text = response_data['choices'][0]['message']['content'].strip()

        # Clean markdown if present
        text = text.replace('``````', '').strip()

        try:
            result = json.loads(text)
        except json.JSONDecodeError as e:
            return JsonResponse({'success': False, 'error': f'AI response parsing failed: {str(e)}'}, status=500)
        
        modified_latex = result.get('modified_latex', latex_code)
        keywords_added = result.get('keywords_added', [])
        match_score = result.get('match_score', 0)
        suggestions = result.get('suggestions', [])
        
        # Calculate changes made
        original_lines = set(latex_code.splitlines())
        modified_lines = set(modified_latex.splitlines())
        changes_made = len(modified_lines - original_lines)
        
        return JsonResponse({
            'success': True,
            'original_latex': latex_code,
            'modified_latex': modified_latex,
            'keywords_added': keywords_added,
            'match_score': match_score,
            'changes_made': changes_made,
            'suggestions': suggestions
        })

    except requests.exceptions.Timeout:
        return JsonResponse({'success': False, 'error': 'AI service timeout. Try again.'}, status=500)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'}, status=500)
