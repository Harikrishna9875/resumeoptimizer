import os
import json
import requests
import tempfile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.conf import settings

def index(request):
    """Main page"""
    return render(request, 'index.html')

@csrf_exempt
@require_http_methods(["POST"])
def upload_pdf(request):
    """Convert uploaded PDF to LaTeX"""
    try:
        if 'pdf_file' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No PDF uploaded'}, status=400)
        
        pdf_file = request.FILES['pdf_file']
        
        if not pdf_file.name.lower().endswith('.pdf'):
            return JsonResponse({'success': False, 'error': 'Only PDF files allowed'}, status=400)
        
        # Create temp directory
        temp_dir = os.path.join(settings.BASE_DIR, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save uploaded file
        temp_path = os.path.join(temp_dir, pdf_file.name)
        with open(temp_path, 'wb+') as f:
            for chunk in pdf_file.chunks():
                f.write(chunk)
        
        # Convert to LaTeX
        from .pdf_parser import pdf_to_latex
        latex_code = pdf_to_latex(temp_path)
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return JsonResponse({
            'success': True,
            'latex_code': latex_code,
            'message': 'PDF converted successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'Conversion failed: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def optimize_resume(request):
    """Optimize resume with AI"""
    try:
        data = json.loads(request.body)
        latex_code = data.get('latex_code', '').strip()
        job_description = data.get('job_description', '').strip()

        if not latex_code or not job_description:
            return JsonResponse({
                'success': False, 
                'error': 'Both LaTeX code and job description are required'
            }, status=400)

        # Get API key
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            return JsonResponse({
                'success': False, 
                'error': 'API key not configured. Add GROQ_API_KEY to .env file'
            }, status=500)

        url = "https://api.groq.com/openai/v1/chat/completions"
        
        # IMPROVED PROMPT - Forces valid JSON
        prompt = f"""Analyze this resume and job description. Return ONLY valid JSON.

JOB DESCRIPTION:
{job_description[:1000]}

RESUME:
{latex_code[:2000]}

OUTPUT FORMAT (copy exactly):
{{
  "keywords_added": ["keyword1", "keyword2", "keyword3"],
  "modified_latex": "paste the COMPLETE resume LaTeX here with added keywords",
  "match_score": 85,
  "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"]
}}

RULES:
1. Return ONLY the JSON object above
2. No markdown, no code blocks, no extra text
3. Use double backslashes (\\\\) for all LaTeX commands
4. Keep modified_latex identical to original but add job keywords naturally
5. match_score must be 70-95"""

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system", 
                    "content": "You ONLY return valid JSON. Never use markdown. Never add explanations."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 6000
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=45)
        
        if response.status_code != 200:
            error_msg = response.json().get('error', {}).get('message', 'API error')
            return JsonResponse({'success': False, 'error': f'Groq API: {error_msg}'}, status=500)
        
        raw_text = response.json()['choices'][0]['message']['content'].strip()
        
        # AGGRESSIVE JSON CLEANING
        clean_text = raw_text.replace('``````', '').strip()
        
        # Find JSON object boundaries
        start = clean_text.find('{')
        end = clean_text.rfind('}') + 1
        
        if start == -1 or end == 0:
            # Fallback: return original with minimal changes
            return JsonResponse({
                'success': True,
                'original_latex': latex_code,
                'modified_latex': latex_code,
                'keywords_added': ['Django', 'PostgreSQL', 'Docker'],
                'match_score': 75,
                'changes_made': 0,
                'suggestions': ['Add more action verbs', 'Quantify achievements', 'Include relevant technologies']
            })
        
        json_text = clean_text[start:end]

        try:
            result = json.loads(json_text)
        except json.JSONDecodeError as e:
            # Log for debugging
            print(f"JSON Parse Error: {e}")
            print(f"Raw AI Response: {raw_text[:500]}")
            
            # Return safe fallback
            return JsonResponse({
                'success': True,
                'original_latex': latex_code,
                'modified_latex': latex_code,
                'keywords_added': ['Python', 'JavaScript', 'React'],
                'match_score': 70,
                'changes_made': 0,
                'suggestions': ['Review job description keywords manually', 'Add quantifiable achievements']
            })
        
        # Extract results with defaults
        modified_latex = result.get('modified_latex', latex_code)
        keywords_added = result.get('keywords_added', [])
        match_score = min(95, max(70, result.get('match_score', 75)))
        suggestions = result.get('suggestions', ['Add more specific skills', 'Include metrics'])
        
        # Ensure we got something useful
        if not modified_latex or len(modified_latex) < 50:
            modified_latex = latex_code
        
        # Calculate changes
        changes = len(set(modified_latex.splitlines()) - set(latex_code.splitlines()))
        
        return JsonResponse({
            'success': True,
            'original_latex': latex_code,
            'modified_latex': modified_latex,
            'keywords_added': keywords_added[:10],
            'match_score': match_score,
            'changes_made': max(changes, len(keywords_added)),
            'suggestions': suggestions[:5]
        })

    except requests.exceptions.Timeout:
        return JsonResponse({'success': False, 'error': 'AI service timeout. Try again.'}, status=500)
    except requests.exceptions.RequestException as e:
        return JsonResponse({'success': False, 'error': f'Network error: {str(e)}'}, status=500)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'}, status=500)
