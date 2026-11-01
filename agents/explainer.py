"""
Agent 3 — Explainer
Uses Gemini to write a clear, impressive explanation of the project
suitable for an industry presentation.
Includes strict schema enforcement & type validation.
"""

from google import genai
from google.genai import types
import json
import os
from dotenv import load_dotenv

load_dotenv()


def normalize_explainer_schema(parsed: dict, analysis: dict) -> dict:
    """Enforces strict string types and minimum array lengths on Explainer output."""
    if not isinstance(parsed, dict):
        parsed = {}

    name = str(analysis.get('project_name', 'This project')).strip()
    p_type = str(analysis.get('project_type', 'software solution')).strip()
    stack = str(analysis.get('tech_stack', 'modern technologies')).strip()

    tagline = str(parsed.get('tagline') or f"{name} — Redefining efficiency through intelligent software.").strip()
    overview = str(parsed.get('overview') or f"{name} is a {p_type} built using {stack}.").strip()
    problem_solved = str(parsed.get('problem_solved') or "Eliminates manual bottlenecks by providing an automated, scalable software solution.").strip()
    how_it_works = str(parsed.get('how_it_works') or f"Built on {stack}, the system coordinates user workflows with secure backend services.").strip()
    tech_highlights = str(parsed.get('tech_highlights') or f"Leverages {stack} for high modularity, responsive UI, and resilient data processing.").strip()
    impact = str(parsed.get('impact') or "Drives productivity and reduces operational overhead for end users.").strip()
    one_liner = str(parsed.get('one_liner') or f"{name} is a {p_type} that automates real-world workflows using {stack}.").strip()

    def ensure_string_list(val, default_list, min_len=3):
        if isinstance(val, list):
            cleaned = [str(x).strip() for x in val if x and str(x).strip()]
            if len(cleaned) >= min_len:
                return cleaned
        return default_list

    default_features = analysis.get('key_features') if isinstance(analysis.get('key_features'), list) and len(analysis.get('key_features', [])) >= 3 else [
        "Automated Workflow Execution", "Secure Data & Access Controls", "Responsive User Dashboard"
    ]
    key_features = ensure_string_list(parsed.get('key_features'), default_features, min_len=3)
    challenges_solved = ensure_string_list(parsed.get('challenges_solved'), ["State Management", "Authentication Security", "Scalable Data Access"], min_len=2)
    future_scope = ensure_string_list(parsed.get('future_scope'), ["Advanced AI Integration", "Mobile Application", "Real-Time Telemetry"], min_len=2)

    return {
        "tagline": tagline,
        "overview": overview,
        "problem_solved": problem_solved,
        "how_it_works": how_it_works,
        "key_features": key_features,
        "tech_highlights": tech_highlights,
        "impact": impact,
        "challenges_solved": challenges_solved,
        "future_scope": future_scope,
        "one_liner": one_liner
    }


def explain_repo(analysis, files):
    """
    Generate a human-readable explanation of the project.
    Returns: strictly-validated explanation dict with guaranteed string fields and lists
    """
    # Extract README if present
    readme = ''
    for path, content in files.items():
        if 'readme' in path.lower():
            readme = content[:2000]
            break

    prompt = f"""You are a professional technical presenter preparing for an industry meeting with an Agentic AI expert.

Based on this project analysis, write a compelling and clear presentation explanation:

Project Analysis:
{json.dumps(analysis, indent=2)}

README Excerpt:
{readme}

Return ONLY a JSON object with these exact fields:
{{
  "tagline": "powerful 8-12 word tagline for the project",
  "overview": "clear 2-3 sentence overview of what this project does and why it matters",
  "problem_solved": "2 sentences on the exact real-world problem this solves",
  "how_it_works": "3 sentences explaining the technical workflow from user action to result",
  "key_features": ["feature 1 with brief benefit", "feature 2", "feature 3", "feature 4", "feature 5"],
  "tech_highlights": "2-3 sentences on what makes the tech stack impressive",
  "impact": "2 sentences on who benefits and how",
  "challenges_solved": ["2-3 technical challenges that were overcome"],
  "future_scope": ["3 specific future enhancements"],
  "one_liner": "a single sentence a student can say confidently in a meeting"
}}

Use confident, professional language. Make it suitable for impressing an Agentic AI industry expert.
Respond with ONLY the JSON object."""

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
        return normalize_explainer_schema(parsed, analysis)
    except Exception as e:
        print(f"Explainer fallback triggered: {e}")
        return normalize_explainer_schema({}, analysis)
