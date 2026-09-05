"""
Agent 4 — Presenter
Uses Gemini to generate structured slide data for a beautiful presentation.
"""

from google import genai
import json
import os
from dotenv import load_dotenv

load_dotenv()


def generate_slides(explanation, analysis, repo_info):
    """
    Generate 7 structured presentation slides.
    Returns: list of slide dicts
    """
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    model = 'gemini-3.6-flash'

    prompt = f"""You are a world-class presentation designer for a tech industry meeting.
Create 7 compelling slides for this software project presentation.

Project: {analysis.get('project_name')}
Tagline: {explanation.get('tagline')}
Type: {analysis.get('project_type')}
Tech Stack: {analysis.get('tech_stack')}
Overview: {explanation.get('overview')}
Problem Solved: {explanation.get('problem_solved')}
How it Works: {explanation.get('how_it_works')}
Key Features: {json.dumps(explanation.get('key_features', []))}
Tech Highlights: {explanation.get('tech_highlights')}
Impact: {explanation.get('impact')}
Future Scope: {json.dumps(explanation.get('future_scope', []))}
GitHub URL: {repo_info.get('url')}
Stars: {repo_info.get('stars')}

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

Respond with ONLY the JSON array, no markdown, no extra text."""

    try:
        response = client.models.generate_content(model=model, contents=prompt)
        text = response.text.strip()
        if '```' in text:
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        slides = json.loads(text.strip())
        # Validate it's a list
        if isinstance(slides, list):
            return slides
    except Exception:
        pass

    # Fallback slides
    name = analysis.get('project_name', 'My Project')
    stack = analysis.get('tech_stack', 'Modern Technologies')
    features = explanation.get('key_features', ['Feature 1', 'Feature 2', 'Feature 3'])
    future = explanation.get('future_scope', ['AI integration', 'Mobile app', 'Analytics'])

    return [
        {
            "title": name,
            "subtitle": explanation.get('tagline', analysis.get('project_type', '')),
            "type": "intro",
            "bullets": [f"🔧 Built with {stack}", f"🌐 {repo_info.get('url')}"],
            "hero_text": explanation.get('one_liner', ''),
            "emoji": "🚀",
            "color_theme": "blue",
            "badge": "LIVE DEMO",
            "narration": f"Welcome to the presentation for {name}. This project is a {analysis.get('project_type')} built with {stack}."
        },
        {
            "title": "The Problem",
            "subtitle": "",
            "type": "problem",
            "bullets": ["❌ Manual processes are slow", "❌ No automated solution exists", "❌ Users need a better way"],
            "hero_text": "",
            "emoji": "❓",
            "color_theme": "orange",
            "badge": "",
            "narration": explanation.get('problem_solved', 'Traditional workflows often rely on manual, time-consuming operations that lack automation.')
        },
        {
            "title": "Our Solution",
            "subtitle": name,
            "type": "solution",
            "bullets": [explanation.get('overview', '')[:80]],
            "hero_text": explanation.get('tagline', ''),
            "emoji": "✅",
            "color_theme": "green",
            "badge": "SOLUTION",
            "narration": explanation.get('overview', f'{name} addresses these challenges by delivering an automated, streamlined software solution.')
        },
        {
            "title": "Key Features",
            "subtitle": "",
            "type": "features",
            "bullets": [f"⭐ {f}" for f in features[:5]],
            "hero_text": "",
            "emoji": "⭐",
            "color_theme": "purple",
            "badge": "",
            "narration": f"Here are the core capabilities of {name}, designed for ease of use, security, and reliability."
        },
        {
            "title": "Tech Stack",
            "subtitle": "",
            "type": "tech",
            "bullets": [f"🔧 {t.strip()}" for t in stack.split(',')[:5]],
            "hero_text": stack,
            "emoji": "💻",
            "color_theme": "teal",
            "badge": "MODERN STACK",
            "narration": f"Under the hood, this project is powered by {stack}, providing modularity, high performance, and scalability."
        },
        {
            "title": "Impact & Demo",
            "subtitle": "",
            "type": "impact",
            "bullets": ["✅ " + explanation.get('impact', 'Saves time and effort')],
            "hero_text": "",
            "emoji": "📊",
            "color_theme": "blue",
            "badge": "LIVE",
            "narration": explanation.get('impact', 'This project significantly streamlines operations, saving time and reducing manual overhead for end users.')
        },
        {
            "title": "Future Roadmap",
            "subtitle": "",
            "type": "future",
            "bullets": [f"🔮 {f}" for f in future[:3]],
            "hero_text": "",
            "emoji": "🔮",
            "color_theme": "purple",
            "badge": "ROADMAP",
            "narration": "Looking ahead, the development roadmap includes introducing AI integrations, mobile support, and deep analytics."
        }
    ]
