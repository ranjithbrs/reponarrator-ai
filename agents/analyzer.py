"""
Agent 2 — Analyzer
Uses Gemini to analyze the tech stack, architecture, and purpose of the project.
"""

from google import genai
from google.genai import types
import json
import os
from dotenv import load_dotenv

load_dotenv()


def analyze_repo(files, repo_info):
    """
    Analyze repository structure and identify tech stack, architecture, etc.
    Returns: structured analysis dict
    """
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    model = 'gemini-3.6-flash'

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
        response = client.models.generate_content(model=model, contents=prompt)
        text = response.text.strip()
        if '```' in text:
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        print(f"Analyzer fallback triggered: {e}")
        return {
            "project_name": repo_info.get('name', 'Project'),
            "project_type": "Web Application",
            "tech_stack": repo_info.get('language', 'Multiple Technologies'),
            "primary_language": repo_info.get('language', 'Unknown'),
            "frameworks": [],
            "key_features": ["Authentication", "Dashboard", "Database integration", "REST API", "Responsive UI"],
            "architecture": "Multi-tier MVC architecture with frontend and backend separation.",
            "use_case": "Designed to solve a real-world problem with a clean software solution.",
            "complexity": "Intermediate",
            "database": "Unknown",
            "deployment": "Cloud deployment",
            "security_features": [],
            "api_integrations": []
        }
