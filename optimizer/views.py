import os
import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from dotenv import load_dotenv

load_dotenv()

def index(request):
    return render(request, 'index.html')

@csrf_exempt
@require_http_methods(["POST"])
def optimize_resume(request):
    try:
        data = json.loads(request.body)
        latex_code = data.get('latex_code', '').strip()
        job_description = data.get('job_description', '').strip()

        if not latex_code or not job_description:
            return JsonResponse({'success': False, 'error': 'Both fields required'}, status=400)

        api_key = os.getenv('GROQ_API_KEY')
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        prompt = f"""You are an ATS resume optimizer. Analyze the job description and enhance the LaTeX resume by adding relevant keywords naturally into existing bullet points. Maintain LaTeX structure.

JOB DESCRIPTION:
{job_description}

ORIGINAL LATEX:
{latex_code}

IMPORTANT: Return ONLY valid JSON with properly escaped backslashes. Use double backslashes in the modified_latex field.
Format: {{"keywords_added": ["keyword1", "keyword2"], "modified_latex": "latex code with \\\\textbf etc", "match_score": 85}}"""

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are an expert ATS resume optimizer. Always return valid JSON with properly escaped LaTeX backslashes."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5,
            "max_tokens": 8000
        }
        
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()
        
        if response.status_code != 200:
            error_msg = response_data.get('error', {}).get('message', 'API error')
            return JsonResponse({'success': False, 'error': error_msg}, status=500)
        
        text = response_data['choices'][0]['message']['content'].strip()

        if '```' in text:
            text = text.replace('```json', '').replace('```', '')

        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Failed to parse AI response'}, status=500)
        
        modified_latex = result.get('modified_latex', latex_code)
        keywords_added = result.get('keywords_added', [])
        match_score = result.get('match_score', 0)
        
        original_lines = set(latex_code.splitlines())
        modified_lines = set(modified_latex.splitlines())
        changes_made = len(modified_lines - original_lines)
        
        return JsonResponse({
            'success': True,
            'original_latex': latex_code,
            'modified_latex': modified_latex,
            'keywords_added': keywords_added,
            'match_score': match_score,
            'changes_made': changes_made
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
