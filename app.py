# RepoNarrator AI — Flask Backend
# 4-Agent Pipeline with Real-Time SSE Streaming and Keep-Alive Heartbeats

import os
import json
import concurrent.futures
from flask import Flask, render_template, request, Response, jsonify, stream_with_context
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


def _event(data: dict) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(data)}\n\n"


def _run_agent_with_heartbeat(agent_id, agent_name, initial_msg, working_prefix, func, *args):
    """
    Executes an agent in a background worker thread while continuously streaming
    SSE keep-alive heartbeats every 1.5 seconds.
    This prevents Gunicorn / Render proxy timeouts (Connection error)
    and provides real-time UI animation to the user.
    """
    yield _event({'agent': agent_id, 'name': agent_name, 'status': initial_msg, 'done': False})

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args)
        step = 0
        dots = ['.', '..', '...', '']
        while True:
            try:
                # Check if agent finished within 1.5 seconds
                res = future.result(timeout=1.5)
                return res
            except concurrent.futures.TimeoutError:
                dot = dots[step % len(dots)]
                step += 1
                yield _event({
                    'agent': agent_id,
                    'name': agent_name,
                    'status': f"{working_prefix}{dot}",
                    'done': False
                })


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
            files, repo_info = yield from _run_agent_with_heartbeat(
                1, 'Fetcher Agent', 'Connecting to GitHub repository...',
                'Fetching repository files from GitHub', fetch_repo, repo_url
            )
            yield _event({'agent': 1, 'name': 'Fetcher Agent',
                          'status': f'Fetched {len(files)} files successfully!', 'done': True})

            # ── Agent 2: Analyze ────────────────────────────────────────────
            analysis = yield from _run_agent_with_heartbeat(
                2, 'Analyzer Agent', 'Initializing Gemini 2.0 / 3.6 Flash...',
                'Analyzing tech stack & architecture', analyze_repo, files, repo_info
            )
            tech = analysis.get('tech_stack', 'multiple technologies')
            yield _event({'agent': 2, 'name': 'Analyzer Agent',
                          'status': f'Detected: {tech}', 'done': True})

            # ── Agent 3: Explain ────────────────────────────────────────────
            explanation = yield from _run_agent_with_heartbeat(
                3, 'Explainer Agent', 'Synthesizing technical narrative...',
                'Writing clear project explanation', explain_repo, analysis, files
            )
            yield _event({'agent': 3, 'name': 'Explainer Agent',
                          'status': 'Project explanation ready!', 'done': True})

            # ── Agent 4: Present ────────────────────────────────────────────
            slides = yield from _run_agent_with_heartbeat(
                4, 'Presenter Agent', 'Structuring Reveal.js deck...',
                'Generating beautiful presentation slides', generate_slides, explanation, analysis, repo_info
            )
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
        'Content-Type': 'text/event-stream; charset=utf-8',
        'Cache-Control': 'no-cache, no-transform',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no',
    }
    return Response(stream_with_context(stream()), headers=headers)


if __name__ == '__main__':
    app.run(debug=True, port=5000, threaded=True)
