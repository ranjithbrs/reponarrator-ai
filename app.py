# RepoNarrator AI — Flask Backend
# Main app with 4-agent pipeline using Server-Sent Events for real-time updates

import os
import json
from flask import Flask, render_template, request, Response, jsonify
from dotenv import load_dotenv
from agents.fetcher import fetch_repo
from agents.analyzer import analyze_repo
from agents.explainer import explain_repo
from agents.presenter import generate_slides

load_dotenv()

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/presentation')
def presentation():
    return render_template('presentation.html')


@app.route('/analyze')
def analyze():
    """
    SSE endpoint — streams agent progress in real time.
    Query param: ?url=<github-repo-url>
    """
    repo_url = request.args.get('url', '').strip()

    if not repo_url:
        return jsonify({'error': 'No URL provided'}), 400

    def stream():
        try:
            # ── Agent 1: Fetch ──────────────────────────────────────────────
            yield _event({'agent': 1, 'name': 'Fetcher Agent',
                          'status': 'Fetching repository files from GitHub...', 'done': False})

            files, repo_info = fetch_repo(repo_url)

            yield _event({'agent': 1, 'name': 'Fetcher Agent',
                          'status': f'Fetched {len(files)} files successfully!', 'done': True})

            # ── Agent 2: Analyze ────────────────────────────────────────────
            yield _event({'agent': 2, 'name': 'Analyzer Agent',
                          'status': 'Analyzing tech stack & architecture...', 'done': False})

            analysis = analyze_repo(files, repo_info)
            tech = analysis.get('tech_stack', 'multiple technologies')

            yield _event({'agent': 2, 'name': 'Analyzer Agent',
                          'status': f'Detected: {tech}', 'done': True})

            # ── Agent 3: Explain ────────────────────────────────────────────
            yield _event({'agent': 3, 'name': 'Explainer Agent',
                          'status': 'Writing clear project explanation...', 'done': False})

            explanation = explain_repo(analysis, files)

            yield _event({'agent': 3, 'name': 'Explainer Agent',
                          'status': 'Project explanation ready!', 'done': True})

            # ── Agent 4: Present ────────────────────────────────────────────
            yield _event({'agent': 4, 'name': 'Presenter Agent',
                          'status': 'Generating beautiful presentation slides...', 'done': False})

            slides = generate_slides(explanation, analysis, repo_info)

            yield _event({'agent': 4, 'name': 'Presenter Agent',
                          'status': f'Generated {len(slides)} slides!', 'done': True})

            # ── Final payload ───────────────────────────────────────────────
            yield _event({
                'complete': True,
                'slides': slides,
                'repo_info': repo_info,
                'analysis': analysis,
                'explanation': explanation
            })

        except Exception as exc:
            yield _event({'error': str(exc)})

    headers = {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no',
    }
    return Response(stream(), headers=headers)


def _event(data: dict) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(data)}\n\n"


if __name__ == '__main__':
    app.run(debug=True, port=5000, threaded=True)
