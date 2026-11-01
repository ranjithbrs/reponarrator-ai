"""
Comprehensive Multi-Repo Pipeline Verification & CI Test Suite
Tests:
1. End-to-End Multi-Repo Pipeline across diverse tech stacks:
   - Python / Flask Web App (CertValid)
   - Java / OOP System (Online-Examination-System)
   - Full-Stack AI Application (secure-ai-journal-app)
2. Rigorous Schema Validation for all 4 Agents.
3. Slide Sequence & Voiceover Narration Completeness (Every slide must have non-empty narration).
4. Error handling & resilience test paths (e.g. Invalid GitHub URLs, 404 repositories).
5. Returns nonzero process exit code (sys.exit(1)) on any test failure for CI gate reliability.
"""

import sys
import os
import json
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.fetcher import (
    fetch_repo,
    parse_github_url,
    GitHubNotFoundError,
    GitHubFetchError
)
from agents.analyzer import analyze_repo
from agents.explainer import explain_repo
from agents.presenter import generate_slides

TEST_REPOS = [
    {
        "name": "Python / Flask Web App",
        "url": "https://github.com/ranjithbrs/CertValid"
    },
    {
        "name": "Java / Spring Boot / OOP",
        "url": "https://github.com/ranjithbrs/Online-Examination-System"
    },
    {
        "name": "Full-Stack AI Project",
        "url": "https://github.com/ranjithbrs/secure-ai-journal-app"
    }
]

EXPECTED_SLIDE_SEQUENCE = ["intro", "problem", "solution", "features", "tech", "impact", "future"]


def validate_analyzer_schema(analysis):
    """Deep validation of Agent 2 output schema."""
    assert isinstance(analysis, dict), f"Analyzer output must be dict, got {type(analysis)}"
    for key in ['project_name', 'project_type', 'tech_stack', 'architecture']:
        assert key in analysis, f"Analyzer missing required field: '{key}'"
        assert analysis[key], f"Analyzer field '{key}' cannot be empty"
    assert 'components' in analysis and isinstance(analysis['components'], list), "Analyzer 'components' must be a list"


def validate_explainer_schema(explanation):
    """Deep validation of Agent 3 output schema."""
    assert isinstance(explanation, dict), f"Explainer output must be dict, got {type(explanation)}"
    required_keys = ['tagline', 'overview', 'problem_solved', 'how_it_works', 'key_features', 'impact']
    for key in required_keys:
        assert key in explanation, f"Explainer missing required field: '{key}'"
        assert explanation[key], f"Explainer field '{key}' cannot be empty"
    assert isinstance(explanation['key_features'], list), "'key_features' must be a list"
    assert len(explanation['key_features']) >= 3, f"Expected >= 3 key features, got {len(explanation['key_features'])}"


def validate_presenter_schema(slides):
    """Deep validation of Agent 4 output schema, sequence, and voice narration."""
    assert isinstance(slides, list), f"Presenter output must be list, got {type(slides)}"
    assert len(slides) == 7, f"Expected exactly 7 slides in deck, got {len(slides)}"

    for idx, slide in enumerate(slides):
        expected_type = EXPECTED_SLIDE_SEQUENCE[idx]
        actual_type = slide.get('type')
        assert actual_type == expected_type, f"Slide #{idx+1} type mismatch. Expected '{expected_type}', got '{actual_type}'"

        # Validate required visual fields
        assert slide.get('title'), f"Slide #{idx+1} is missing 'title'"
        assert isinstance(slide.get('bullets', []), list), f"Slide #{idx+1} 'bullets' must be list"
        assert len(slide.get('bullets', [])) > 0, f"Slide #{idx+1} 'bullets' cannot be empty"
        assert slide.get('color_theme') in ['blue', 'purple', 'green', 'teal', 'orange'], \
            f"Slide #{idx+1} has invalid color theme: '{slide.get('color_theme')}'"

        # Validate voice narration completeness
        narration = slide.get('narration', '')
        assert isinstance(narration, str) and len(narration.strip()) >= 15, \
            f"Slide #{idx+1} ({actual_type}) is missing a valid voice narration script (found {len(narration)} chars)"


def test_error_handling_paths():
    """Validates that fetcher throws clean structured exceptions on invalid / nonexistent targets."""
    print("\n--- Testing Error Handling & Failure Paths ---")

    # 1. Invalid URL string
    try:
        parse_github_url("not-a-valid-github-url")
        raise AssertionError("Failed to reject invalid GitHub URL")
    except ValueError:
        print("  [✓] Successfully caught ValueError on malformed URL")

    # 2. Non-existent / private repository (HTTP 404)
    try:
        fetch_repo("https://github.com/ranjithbrs/nonexistent-audit-repo-404xyz")
        raise AssertionError("Failed to raise GitHubNotFoundError on 404 repo")
    except GitHubNotFoundError as e:
        assert "not found" in str(e).lower()
        print("  [✓] Successfully caught structured GitHubNotFoundError on 404 target")


def run_suite():
    print("=" * 65)
    print("🧪 REPONARRATOR AI — RIGOROUS MULTI-AGENT VERIFICATION SUITE")
    print("=" * 65)

    all_passed = True
    results = []

    # 1. Run unit error-handling tests
    try:
        test_error_handling_paths()
    except Exception as e:
        print(f"  ❌ Error path test failed: {e}")
        all_passed = False

    # 2. Run multi-repository end-to-end tests
    print("\n--- Testing End-to-End Multi-Repo Pipeline ---")
    for i, item in enumerate(TEST_REPOS, 1):
        print(f"\n[{i}/{len(TEST_REPOS)}] Testing: {item['name']}")
        print(f"      Repository: {item['url']}")
        t0 = time.time()

        try:
            # Agent 1: Fetcher
            files, repo_info = fetch_repo(item['url'])
            file_count = len(files)
            print(f"  [✓] Agent 1 (Fetcher): Fetched {file_count} files | Branch: {repo_info.get('default_branch')} | Stars: {repo_info.get('stars', 0)}")
            assert file_count > 0, "No files fetched from repository"

            # Agent 2: Analyzer
            analysis = analyze_repo(files, repo_info)
            validate_analyzer_schema(analysis)
            print(f"  [✓] Agent 2 (Analyzer): Verified schema for '{analysis['project_name']}' | Tech: {analysis['tech_stack']}")

            # Agent 3: Explainer
            explanation = explain_repo(analysis, files)
            validate_explainer_schema(explanation)
            print(f"  [✓] Agent 3 (Explainer): Verified schema | Tagline: '{explanation['tagline']}'")

            # Agent 4: Presenter
            slides = generate_slides(explanation, analysis, repo_info)
            validate_presenter_schema(slides)
            print(f"  [✓] Agent 4 (Presenter): Verified all 7 slides with complete voice narration scripts")

            elapsed = round(time.time() - t0, 2)
            print(f"  🎉 Pass! Pipeline and schema validated in {elapsed}s")
            results.append({"name": item['name'], "status": "PASSED", "time": elapsed})

        except Exception as e:
            elapsed = round(time.time() - t0, 2)
            print(f"  ❌ Failed: {str(e)} ({elapsed}s)")
            results.append({"name": item['name'], "status": f"FAILED: {e}", "time": elapsed})
            all_passed = False

    # 3. Print Final Report
    print("\n" + "=" * 65)
    print("📊 MULTI-AGENT VERIFICATION SUMMARY REPORT")
    print("=" * 65)
    for r in results:
        icon = "✅" if r["status"] == "PASSED" else "❌"
        print(f"{icon} {r['name']}: {r['status']} ({r['time']}s)")

    if all_passed:
        print("\n🌟 ALL TESTS & RIGOROUS SCHEMAS PASSED! Pipeline is fully production-ready.")
        sys.exit(0)
    else:
        print("\n❌ CI GATE FAILED: Some tests or schema assertions failed.")
        sys.exit(1)


if __name__ == '__main__':
    run_suite()
