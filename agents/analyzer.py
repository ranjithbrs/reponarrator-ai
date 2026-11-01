"""
Agent 2 — Analyzer
Uses Gemini to analyze the tech stack, architecture, and purpose of the project.
Includes strict schema enforcement & type validation.
"""

from google import genai
from google.genai import types
import json
import os
from dotenv import load_dotenv

load_dotenv()


def normalize_analyzer_schema(parsed: dict, repo_info: dict) -> dict:
    """Enforces strict types and non-empty values on all Analyzer fields."""
    if not isinstance(parsed, dict):
        parsed = {}

    name = str(parsed.get('project_name') or repo_info.get('name') or 'Project').strip()
    p_type = str(parsed.get('project_type') or 'Web Application').strip()
    
    # tech_stack normalization
    raw_stack = parsed.get('tech_stack') or repo_info.get('language') or 'Modern Technologies'
    if isinstance(raw_stack, list):
        tech_stack = ', '.join([str(x).strip() for x in raw_stack if x])
    else:
        tech_stack = str(raw_stack).strip()

    primary_lang = str(parsed.get('primary_language') or repo_info.get('language') or 'Unknown').strip()
    
    architecture = str(parsed.get('architecture') or 'Multi-tier modular architecture with clear separation of concerns.').strip()
    use_case = str(parsed.get('use_case') or 'Engineered to deliver automated, reliable software operations.').strip()
    complexity = str(parsed.get('complexity') or 'Intermediate').strip()
    database = str(parsed.get('database') or 'Unknown').strip()
    deployment = str(parsed.get('deployment') or 'Cloud deployment').strip()

    # List fields enforcement
    def ensure_string_list(val, default_list):
        if isinstance(val, list):
            res = [str(x).strip() for x in val if x and str(x).strip()]
            if res:
                return res
        return default_list

    frameworks = ensure_string_list(parsed.get('frameworks'), [])
    components = ensure_string_list(parsed.get('components'), ["Client Interface", "Core Business Logic", "Data Storage"])
    key_features = ensure_string_list(parsed.get('key_features'), [
        "Authentication & Security", "Interactive Dashboard", "Database integration", "REST API", "Responsive UI"
    ])
    security_features = ensure_string_list(parsed.get('security_features'), [])
    api_integrations = ensure_string_list(parsed.get('api_integrations'), [])

    return {
        "project_name": name,
        "project_type": p_type,
        "tech_stack": tech_stack,
        "primary_language": primary_lang,
        "frameworks": frameworks,
        "components": components,
        "key_features": key_features,
        "architecture": architecture,
        "use_case": use_case,
        "complexity": complexity,
        "database": database,
        "deployment": deployment,
        "security_features": security_features,
        "api_integrations": api_integrations
    }


def analyze_repo(files, repo_info):
    """
    Analyze repository structure and identify tech stack, architecture, etc.
    Returns: strictly-validated structured analysis dict
    """
    file_list = list(files.keys())

    # Sample first 500 chars of up to 12 key files
    file_samples = {}
    for path, content in list(files.items())[:12]:
        file_samples[path] = content[:500]

    prompt = f"""You are a senior software architect. Analyze this GitHub repository.

Repository Name: {repo_info.get('name')}
Description: {repo_info.get('description', 'Not provided')}
Primary Language: {repo_info.get('language', 'Unknown')}
Topics: {', '.join(repo_info.get('topics', []))}
Homepage: {repo_info.get('homepage', 'None')}

All files in repo:
{json.dumps(file_list, indent=2)}

Sample file contents (first 500 chars each):
{json.dumps(file_samples, indent=2)}

Return ONLY a JSON object with these exact fields:
{{
  "project_name": "clean project name",
  "project_type": "e.g. Web App, REST API, CLI Tool, Desktop App, Mobile App, AI/ML App",
  "tech_stack": "comma-separated technologies e.g. Python, Flask, MySQL, JavaScript",
  "primary_language": "main programming language",
  "frameworks": ["Framework1", "Framework2"],
  "components": ["Frontend UI", "Backend API", "Authentication Module", "Database Layer"],
  "key_features": ["feature 1", "feature 2", "feature 3", "feature 4", "feature 5"],
  "architecture": "2-3 sentence description of the architecture pattern",
  "use_case": "1-2 sentences on who uses this and why",
  "complexity": "Simple or Intermediate or Advanced",
  "database": "database name or None",
  "deployment": "deployment platform or Unknown",
  "security_features": ["any security features or empty array"],
  "api_integrations": ["any APIs or empty array"]
}}

Respond with ONLY the JSON object, no markdown, no explanation."""

    try:
        api_key = os.getenv('GEMINI_API_KEY', '').strip()
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set.")

        client = genai.Client(api_key=api_key)
        model = 'gemini-3.6-flash'

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        text = response.text.strip()
        if '```' in text:
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        parsed = json.loads(text.strip())
        return normalize_analyzer_schema(parsed, repo_info)
    except Exception as e:
        print(f"Analyzer fallback triggered: {e}")
        return normalize_analyzer_schema({}, repo_info)
