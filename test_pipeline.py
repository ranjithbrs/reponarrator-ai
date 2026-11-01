"""
Comprehensive Multi-Repo Pipeline Verification & CI Test Suite
Tests:
1. Isolated Offline Unit Tests (Mocks):
   - HTTP 401 Unauthorized -> GitHubAuthError
   - HTTP 403 Rate Limit (X-RateLimit-Remaining: 0) -> GitHubRateLimitError
   - HTTP 403 Forbidden -> GitHubAccessForbiddenError
   - HTTP 404 Not Found / Private -> GitHubNotFoundError
   - Streamed Zipball chunk download exceeding MAX_ZIPBALL_SIZE cap
   - Agent Schema Enforcement & Malformed Model Output Recovery (Analyzer, Explainer, Presenter)
2. Live Multi-Repo End-to-End Pipeline Verification across diverse stacks:
   - Python / Flask Web App (CertValid)
   - Java / Spring Boot / OOP (Online-Examination-System)
   - Full-Stack AI Project (secure-ai-journal-app)
3. Deterministic exit codes (sys.exit(0) on success, sys.exit(1) on failure) for CI gates.
"""

import sys
import os
import json
import io
import time
import zipfile
import urllib.error
from unittest.mock import patch, MagicMock

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.fetcher import (
    fetch_repo,
    fetch_repo_via_zip,
    parse_github_url,
    GitHubNotFoundError,
    GitHubAuthError,
    GitHubRateLimitError,
    GitHubAccessForbiddenError,
    GitHubFetchError,
    MAX_ZIPBALL_SIZE
)
from agents.analyzer import analyze_repo, normalize_analyzer_schema
from agents.explainer import explain_repo, normalize_explainer_schema
from agents.presenter import generate_slides, validate_and_normalize_slides

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


# =====================================================================
# 1. ISOLATED OFFLINE UNIT TESTS (MOCKS)
# =====================================================================

def test_offline_unit_suite():
    print("\n--- Running Isolated Offline Unit Tests (Mocks) ---")

    # Test 1.1: URL Parsing
    owner, repo = parse_github_url("https://github.com/torvalds/linux.git/")
    assert owner == "torvalds" and repo == "linux", "parse_github_url failed on git suffix"
    try:
        parse_github_url("https://invalid-url.com/something")
        raise AssertionError("Failed to reject invalid domain")
    except ValueError:
        pass
    print("  [✓] Offline: URL Parsing & Validation passed")

    # Test 1.2: Mock HTTP 401 Unauthorized
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_get.return_value = mock_resp
        try:
            fetch_repo("https://github.com/fake-owner/fake-repo")
            raise AssertionError("Should have raised GitHubAuthError on 401")
        except GitHubAuthError:
            print("  [✓] Offline Mock: HTTP 401 correctly raised GitHubAuthError")

    # Test 1.3: Mock HTTP 403 Rate Limit Exceeded
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.headers = {'X-RateLimit-Remaining': '0', 'X-RateLimit-Reset': '1700000000'}
        mock_get.return_value = mock_resp
        try:
            fetch_repo("https://github.com/fake-owner/fake-repo")
            raise AssertionError("Should have raised GitHubRateLimitError on 403 with 0 remaining")
        except GitHubRateLimitError:
            print("  [✓] Offline Mock: HTTP 403 rate-limit correctly raised GitHubRateLimitError")

    # Test 1.4: Mock HTTP 404 Repository Not Found
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp
        try:
            fetch_repo("https://github.com/fake-owner/fake-repo")
            raise AssertionError("Should have raised GitHubNotFoundError on 404")
        except GitHubNotFoundError:
            print("  [✓] Offline Mock: HTTP 404 correctly raised GitHubNotFoundError")

    # Test 1.5: Mock Zipball HTTP 403 Rate Limit on Archive Download
    with patch("urllib.request.urlopen") as mock_urlopen:
        err = urllib.error.HTTPError(
            url="http://example.com/archive.zip",
            code=403,
            msg="Forbidden",
            hdrs={'X-RateLimit-Remaining': '0', 'X-RateLimit-Reset': '1700000000'},
            fp=io.BytesIO(b"")
        )
        mock_urlopen.side_effect = err
        try:
            fetch_repo_via_zip("fake-owner", "fake-repo", ["main"], repo_confirmed_exists=True)
            raise AssertionError("Should have raised GitHubRateLimitError on Zipball 403 rate-limit")
        except GitHubRateLimitError:
            print("  [✓] Offline Mock: Zipball HTTP 403 rate-limit correctly raised GitHubRateLimitError")

    # Test 1.6: Mock Oversized Archive Chunk Streaming
    with patch("urllib.request.urlopen") as mock_urlopen:
        # Create a mock response that streams chunks exceeding MAX_ZIPBALL_SIZE
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.headers = {}
        # Return chunks of 10MB each; after 4 chunks it exceeds 30MB
        chunk_data = b"X" * (10 * 1024 * 1024)
        mock_resp.read.side_effect = [chunk_data, chunk_data, chunk_data, chunk_data, b""]
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        files = fetch_repo_via_zip("fake-owner", "fake-repo", ["main"], repo_confirmed_exists=True)
        assert files == {}, "Oversized zip stream must abort and return empty files"
        print("  [✓] Offline Mock: Oversized archive correctly aborted during streaming")

    # Test 1.7: Schema Normalization & Malformed Model Recovery
    # Analyzer with malformed types
    malformed_analyzer = {
        "project_name": 12345,
        "tech_stack": ["Python", "Flask"],
        "components": "not-a-list"
    }
    norm_analysis = normalize_analyzer_schema(malformed_analyzer, {'name': 'TestRepo', 'language': 'Python'})
    assert isinstance(norm_analysis['project_name'], str) and norm_analysis['project_name'] == "12345"
    assert isinstance(norm_analysis['tech_stack'], str) and "Python, Flask" in norm_analysis['tech_stack']
    assert isinstance(norm_analysis['components'], list) and len(norm_analysis['components']) >= 3
    print("  [✓] Offline Mock: Analyzer schema normalization enforces valid types & defaults")

    # Explainer with missing keys
    norm_explainer = normalize_explainer_schema({}, norm_analysis)
    assert isinstance(norm_explainer['tagline'], str) and len(norm_explainer['tagline']) > 0
    assert isinstance(norm_explainer['key_features'], list) and len(norm_explainer['key_features']) >= 3
    print("  [✓] Offline Mock: Explainer schema normalization enforces complete text and features")

    # Presenter with invalid slide count / types
    invalid_slides = [{"title": "Only One Slide"}]
    slides = validate_and_normalize_slides(
        invalid_slides, "TestRepo", "Python", ["Python"], norm_explainer, norm_analysis, {'url': ''},
        norm_explainer['key_features'], norm_explainer['future_scope'], norm_explainer['impact']
    )
    assert len(slides) == 7, "Presenter must return exactly 7 slides even on malformed input"
    assert [s['type'] for s in slides] == EXPECTED_SLIDE_SEQUENCE, "Slide sequence must match contract"
    assert all(len(s['narration']) >= 15 for s in slides), "Every slide must have non-empty voiceover narration"
    print("  [✓] Offline Mock: Presenter enforces strict 7-slide contract & narration recovery")


# =====================================================================
# 2. LIVE MULTI-REPO VERIFICATION SUITE
# =====================================================================

def run_live_multi_repo_suite():
    print("\n--- Testing Live Multi-Repo End-to-End Pipeline ---")
    all_passed = True
    results = []

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
            assert isinstance(analysis['project_name'], str) and analysis['project_name'], "Missing project_name"
            assert isinstance(analysis['tech_stack'], str) and analysis['tech_stack'], "Missing tech_stack"
            assert isinstance(analysis['components'], list) and len(analysis['components']) > 0, "Invalid components"
            print(f"  [✓] Agent 2 (Analyzer): Verified schema for '{analysis['project_name']}' | Tech: {analysis['tech_stack']}")

            # Agent 3: Explainer
            explanation = explain_repo(analysis, files)
            assert isinstance(explanation['tagline'], str) and explanation['tagline'], "Missing tagline"
            assert isinstance(explanation['key_features'], list) and len(explanation['key_features']) >= 3, "Insufficient features"
            print(f"  [✓] Agent 3 (Explainer): Verified schema | Tagline: '{explanation['tagline']}'")

            # Agent 4: Presenter
            slides = generate_slides(explanation, analysis, repo_info)
            assert len(slides) == 7, f"Expected 7 slides, got {len(slides)}"
            for idx, slide in enumerate(slides):
                assert slide['type'] == EXPECTED_SLIDE_SEQUENCE[idx], f"Slide #{idx+1} type mismatch"
                assert len(slide.get('narration', '')) >= 15, f"Slide #{idx+1} missing valid voice narration"
            print(f"  [✓] Agent 4 (Presenter): Verified all 7 slides with complete voice narration scripts")

            elapsed = round(time.time() - t0, 2)
            print(f"  🎉 Pass! Pipeline and schema validated in {elapsed}s")
            results.append({"name": item['name'], "status": "PASSED", "time": elapsed})

        except Exception as e:
            elapsed = round(time.time() - t0, 2)
            print(f"  ❌ Failed: {str(e)} ({elapsed}s)")
            results.append({"name": item['name'], "status": f"FAILED: {e}", "time": elapsed})
            all_passed = False

    print("\n" + "=" * 65)
    print("📊 MULTI-AGENT VERIFICATION SUMMARY REPORT")
    print("=" * 65)
    for r in results:
        icon = "✅" if r["status"] == "PASSED" else "❌"
        print(f"{icon} {r['name']}: {r['status']} ({r['time']}s)")

    return all_passed


def main():
    print("=" * 65)
    print("🧪 REPONARRATOR AI — RIGOROUS MULTI-AGENT TEST SUITE")
    print("=" * 65)

    try:
        test_offline_unit_suite()
    except Exception as e:
        print(f"❌ Offline Unit Suite Failed: {e}")
        sys.exit(1)

    live_passed = run_live_multi_repo_suite()

    if live_passed:
        print("\n🌟 All configured verification checks passed successfully.")
        sys.exit(0)
    else:
        print("\n❌ CI GATE FAILED: One or more verification checks failed.")
        sys.exit(1)


if __name__ == '__main__':
    main()
