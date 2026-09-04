"""
Agent 3 — Explainer
Uses Gemini to write a clear, impressive explanation of the project
suitable for an industry presentation.
"""

from google import genai
import json
import os
from dotenv import load_dotenv

load_dotenv()


def explain_repo(analysis, files):
    """
    Generate a human-readable explanation of the project.
    Returns: explanation dict with sections
    """
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    model = 'gemini-3.6-flash'

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

README Content (if available):
{readme if readme else 'Not available'}

Write an impressive, clear explanation as a JSON object with EXACTLY these keys:
{{
  "tagline": "one powerful sentence describing the project (like a product tagline)",
  "overview": "2-3 sentences explaining what this project is in simple language",
  "problem_solved": "2-3 sentences on the real-world problem this solves",
  "how_it_works": "3-4 sentences explaining how it technically works",
  "key_features": ["5 specific impressive features with details"],
  "tech_highlights": "2-3 sentences on what makes the tech stack impressive",
  "impact": "2 sentences on who benefits and how",
  "challenges_solved": ["2-3 technical challenges that were overcome"],
  "future_scope": ["3 specific future enhancements"],
  "one_liner": "a single sentence a student can say confidently in a meeting"
}}

Use confident, professional language. Make it suitable for impressing an Agentic AI industry expert.
Respond with ONLY the JSON object."""

    try:
        response = client.models.generate_content(model=model, contents=prompt)
        text = response.text.strip()
        if '```' in text:
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        print(f"Explainer fallback triggered: {e}")
        name = analysis.get('project_name', 'This project')
        stack = analysis.get('tech_stack', 'modern technologies')
        return {
            "tagline": f"{name} — Redefining efficiency through intelligent software.",
            "overview": f"{name} is a {analysis.get('project_type')} built using {stack}.",
            "problem_solved": "It addresses a key real-world problem with an automated software solution.",
            "how_it_works": f"Built on {stack}, the system processes user input and delivers results through a clean interface.",
            "key_features": analysis.get('key_features', ['Feature 1', 'Feature 2', 'Feature 3']),
            "tech_highlights": f"The use of {stack} ensures scalability, security, and performance.",
            "impact": "Saves time and reduces manual effort for end users significantly.",
            "challenges_solved": ["Data consistency", "User authentication", "Scalable architecture"],
            "future_scope": ["AI integration", "Mobile app", "Analytics dashboard"],
            "one_liner": f"{name} is a {analysis.get('project_type')} that automates real-world workflows using {stack}."
        }
