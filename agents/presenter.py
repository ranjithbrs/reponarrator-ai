"""
Agent 4 — Presenter
Uses Gemini to generate structured slide data for a beautiful presentation.
"""

from google import genai
from google.genai import types
import json
import os
from dotenv import load_dotenv

load_dotenv()


def generate_slides(explanation, analysis, repo_info):
    """
    Generate 7 structured presentation slides.
    Returns: list of slide dicts
    """
    name = str(analysis.get('project_name') or repo_info.get('name') or 'Project')
    
    # Safe tech stack handling
    stack_raw = analysis.get('tech_stack', 'Modern Technologies')
    if isinstance(stack_raw, list):
        stack_list = [str(x) for x in stack_raw if x]
        stack_str = ', '.join(stack_list)
    elif isinstance(stack_raw, str):
        stack_list = [s.strip() for s in stack_raw.split(',') if s.strip()]
        stack_str = stack_raw
    else:
        stack_list = ['Modern Technologies']
        stack_str = 'Modern Technologies'

    if not stack_list:
        stack_list = ['Python', 'Modern Software Architecture']

    # Safe features handling
    features_raw = explanation.get('key_features') or analysis.get('key_features') or ['Clean Architecture', 'REST API', 'Responsive UI']
    if isinstance(features_raw, list):
        features = [str(f) for f in features_raw if f]
    else:
        features = [str(features_raw)]

    # Safe future scope handling
    future_raw = explanation.get('future_scope') or ['Cloud Scalability', 'Advanced AI Features', 'Automated Testing']
    if isinstance(future_raw, list):
        future = [str(f) for f in future_raw if f]
    else:
        future = [str(future_raw)]

    # Safe impact handling
    impact_raw = explanation.get('impact') or 'Significantly streamlines operations and saves manual effort.'
    if isinstance(impact_raw, list):
        impact_str = ' '.join(str(x) for x in impact_raw)
    else:
        impact_str = str(impact_raw)

    prompt = f"""You are a world-class presentation designer for a tech industry meeting.
Create 7 compelling slides for this software project presentation.

Project: {name}
Tagline: {explanation.get('tagline', '')}
Type: {analysis.get('project_type', 'Software Application')}
Tech Stack: {stack_str}
Overview: {explanation.get('overview', '')}
Problem Solved: {explanation.get('problem_solved', '')}
How it Works: {explanation.get('how_it_works', '')}
Key Features: {json.dumps(features)}
Tech Highlights: {explanation.get('tech_highlights', '')}
Impact: {impact_str}
Future Scope: {json.dumps(future)}
GitHub URL: {repo_info.get('url', '')}
Stars: {repo_info.get('stars', 0)}

Return a JSON array of EXACTLY 7 slide objects. Each slide must have:
- "title": short slide title (max 6 words)
- "subtitle": optional subtitle or empty string
- "type": one of ["intro", "problem", "solution", "features", "tech", "impact", "future"]
- "bullets": array of 3-5 bullet points (each max 10 words, start with emoji)
- "hero_text": one big bold statement for the slide (optional, can be empty string)
- "emoji": single emoji representing the slide
- "color_theme": one of ["blue", "purple", "green", "teal", "orange"]
- "badge": short badge text like "LIVE" or "AI-POWERED" or "OPEN SOURCE" or empty string
- "narration": 2 to 3 natural spoken sentences explaining this slide out loud to the audience in clear, engaging English

Slide sequence must be:
1. intro - Title slide with project name and tagline
2. problem - The problem this solves
3. solution - How this project solves it
4. features - Key features
5. tech - Technology stack
6. impact - Real-world impact and demo info
7. future - Future roadmap

Respond with ONLY the JSON array."""

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
        slides = json.loads(text)
        if isinstance(slides, list) and len(slides) >= 4:
            return slides
    except Exception as e:
        print(f"Presenter fallback triggered: {e}")

    # Fallback slides — 100% resilient and safe
    return [
        {
            "title": name,
            "subtitle": str(explanation.get('tagline') or analysis.get('project_type') or 'Software System'),
            "type": "intro",
            "bullets": [f"🔧 Built with {stack_str[:60]}", f"🌐 {repo_info.get('url', 'GitHub Open Source')}"],
            "hero_text": str(explanation.get('one_liner') or f"Introducing {name}"),
            "emoji": "🚀",
            "color_theme": "blue",
            "badge": "LIVE DEMO",
            "narration": f"Welcome to the presentation for {name}. This project is a {analysis.get('project_type', 'software platform')} built with {stack_str}."
        },
        {
            "title": "The Problem",
            "subtitle": "Current Workflow Inefficiencies",
            "type": "problem",
            "bullets": ["❌ Manual processes are time consuming", "❌ Lack of automated verification", "❌ Users need a modern solution"],
            "hero_text": "Overcoming traditional operational bottlenecks.",
            "emoji": "❓",
            "color_theme": "orange",
            "badge": "CHALLENGE",
            "narration": str(explanation.get('problem_solved') or 'Traditional workflows often rely on manual, time-consuming operations that lack automation.')
        },
        {
            "title": "Our Solution",
            "subtitle": f"{name} Architecture",
            "type": "solution",
            "bullets": [str(explanation.get('overview', f'{name} addresses core bottlenecks with software automation.'))[:100]],
            "hero_text": str(explanation.get('tagline') or f"Automating workflows with {name}"),
            "emoji": "✅",
            "color_theme": "green",
            "badge": "SOLUTION",
            "narration": str(explanation.get('overview') or f'{name} addresses these challenges by delivering an automated, streamlined software solution.')
        },
        {
            "title": "Key Features",
            "subtitle": "Core Capabilities",
            "type": "features",
            "bullets": [f"⭐ {f}" for f in features[:5]],
            "hero_text": "Engineered for high performance and reliability.",
            "emoji": "⭐",
            "color_theme": "purple",
            "badge": "FEATURES",
            "narration": f"Here are the core capabilities of {name}, designed for ease of use, security, and reliability."
        },
        {
            "title": "Tech Stack",
            "subtitle": "Under the Hood",
            "type": "tech",
            "bullets": [f"🔧 {t}" for t in stack_list[:5]],
            "hero_text": stack_str,
            "emoji": "💻",
            "color_theme": "teal",
            "badge": "MODERN STACK",
            "narration": f"Under the hood, this project is powered by {stack_str}, providing modularity, high performance, and scalability."
        },
        {
            "title": "Impact & Demo",
            "subtitle": "Value Delivered",
            "type": "impact",
            "bullets": [f"✅ {impact_str[:120]}"],
            "hero_text": "Delivering measurable time savings.",
            "emoji": "📊",
            "color_theme": "blue",
            "badge": "IMPACT",
            "narration": impact_str
        },
        {
            "title": "Future Roadmap",
            "subtitle": "What Lies Ahead",
            "type": "future",
            "bullets": [f"🔮 {f}" for f in future[:3]],
            "hero_text": "Continuous innovation and feature expansion.",
            "emoji": "🔮",
            "color_theme": "purple",
            "badge": "ROADMAP",
            "narration": "Looking ahead, the development roadmap includes introducing deep AI integrations, mobile client support, and real-time analytics."
        }
    ]
