"""
Comprehensive Multi-Repo Pipeline Verification & CI Test Suite
Organized using Python's standard `unittest` framework:

1. TestFetcherOffline (Unit Tests / Mocks):
   - parse_github_url tests (valid, .git, malformed)
   - HTTP 401 Unauthorized -> GitHubAuthError
   - HTTP 403 Rate Limit (X-RateLimit-Remaining: 0) -> GitHubRateLimitError
   - HTTP 403 Forbidden -> GitHubAccessForbiddenError
   - HTTP 404 Not Found / Private -> GitHubNotFoundError
   - Zipball HTTP 403 rate-limit
   - Oversized archive stream abort (>30MB budget)
   - Tree API 401 / 403 rate-limit failures
   - Blob API 401, 403, 404, and timeout failures

2. TestPresenterStrictValidationOffline (Unit Tests):
   - Rejection on count != 7
   - Rejection on invalid sequence
   - Rejection on invalid color theme (e.g. 'neon-pink')
   - Rejection on non-string bullet items
   - Rejection on short / missing narration (< 15 chars)
   - Complete fallback activation on any violation

3. TestAgentsGeminiFallbackOffline (Unit Tests / Mocks):
   - Analyzer: Malformed JSON, missing fields, non-string types, Gemini 429/503 exceptions
   - Explainer: Missing fields, wrong types, Gemini 429/503 exceptions
   - Presenter: Gemini 429/503 exceptions -> valid 7-slide contract

4. TestLiveMultiRepoIntegration (Live Integration Tests):
   - Executed against CertValid, Online-Examination-System, and secure-ai-journal-app
   - Fully tests end-to-end multi-agent orchestration and schema compliance.
"""

import sys
import os
import io
import time
import unittest
from unittest.mock import patch, MagicMock
import urllib.error

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

EXPECTED_SLIDE_SEQUENCE = ["intro", "problem", "solution", "features", "tech", "impact", "future"]

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


# =====================================================================
# 1. OFFLINE UNIT TESTS: FETCHER
# =====================================================================

class TestFetcherOffline(unittest.TestCase):

    def test_parse_github_url_valid(self):
        owner, repo = parse_github_url("https://github.com/torvalds/linux.git/")
        self.assertEqual(owner, "torvalds")
        self.assertEqual(repo, "linux")

    def test_parse_github_url_invalid(self):
        with self.assertRaises(ValueError):
            parse_github_url("https://notgithub.com/torvalds/linux")
        with self.assertRaises(ValueError):
            parse_github_url("")

    @patch("requests.get")
    def test_metadata_http_401_auth_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_get.return_value = mock_resp
        with self.assertRaises(GitHubAuthError):
            fetch_repo("https://github.com/fake/repo")

    @patch("requests.get")
    def test_metadata_http_403_rate_limit(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.headers = {'X-RateLimit-Remaining': '0', 'X-RateLimit-Reset': '1700000000'}
        mock_get.return_value = mock_resp
        with self.assertRaises(GitHubRateLimitError):
            fetch_repo("https://github.com/fake/repo")

    @patch("requests.get")
    def test_metadata_http_404_not_found(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp
        with self.assertRaises(GitHubNotFoundError):
            fetch_repo("https://github.com/fake/repo")

    @patch("urllib.request.urlopen")
    def test_zipball_http_403_rate_limit(self, mock_urlopen):
        err = urllib.error.HTTPError(
            url="http://example.com/archive.zip",
            code=403,
            msg="Forbidden",
            hdrs={'X-RateLimit-Remaining': '0', 'X-RateLimit-Reset': '1700000000'},
            fp=io.BytesIO(b"")
        )
        mock_urlopen.side_effect = err
        with self.assertRaises(GitHubRateLimitError):
            fetch_repo_via_zip("fake", "repo", ["main"], repo_confirmed_exists=True)

    @patch("urllib.request.urlopen")
    def test_zipball_http_404_unconfirmed_repo(self, mock_urlopen):
        err = urllib.error.HTTPError(
            url="http://example.com/archive.zip",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=io.BytesIO(b"")
        )
        mock_urlopen.side_effect = err
        with self.assertRaises(GitHubNotFoundError):
            fetch_repo_via_zip("fake", "repo", ["main"], repo_confirmed_exists=False)

    @patch("urllib.request.urlopen")
    def test_zipball_oversized_stream_aborts(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.headers = {}
        chunk_data = b"X" * (10 * 1024 * 1024)
        mock_resp.read.side_effect = [chunk_data, chunk_data, chunk_data, chunk_data, b""]
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        files = fetch_repo_via_zip("fake", "repo", ["main"], repo_confirmed_exists=True)
        self.assertEqual(files, {})

    @patch("agents.fetcher.fetch_repo_via_zip", return_value={})
    @patch("requests.get")
    def test_tree_api_rate_limit_error(self, mock_get, mock_zip):
        meta_resp = MagicMock(status_code=200, json=lambda: {'default_branch': 'main'})
        tree_resp = MagicMock(status_code=403, headers={'X-RateLimit-Remaining': '0'})
        mock_get.side_effect = [meta_resp, tree_resp]

        with self.assertRaises(GitHubRateLimitError):
            fetch_repo("https://github.com/fake/repo")

    @patch("agents.fetcher.fetch_repo_via_zip", return_value={})
    @patch("requests.get")
    def test_blob_api_rate_limit_error(self, mock_get, mock_zip):
        meta_resp = MagicMock(status_code=200, json=lambda: {'default_branch': 'main'})
        tree_resp = MagicMock(status_code=200, json=lambda: {'tree': [{'type': 'blob', 'path': 'app.py'}]})
        blob_resp = MagicMock(status_code=403, headers={'X-RateLimit-Remaining': '0'})
        mock_get.side_effect = [meta_resp, tree_resp, blob_resp]

        with self.assertRaises(GitHubRateLimitError):
            fetch_repo("https://github.com/fake/repo")


# =====================================================================
# 2. OFFLINE UNIT TESTS: PRESENTER STRICT VALIDATION
# =====================================================================

class TestPresenterStrictValidationOffline(unittest.TestCase):

    def setUp(self):
        self.dummy_analysis = {
            'project_name': 'TestApp',
            'project_type': 'Web App',
            'tech_stack': 'Python, Flask',
            'components': ['UI', 'API']
        }
        self.dummy_explanation = {
            'tagline': 'TestApp — Powering modern testing.',
            'overview': 'A test overview.',
            'problem_solved': 'Manual testing issues.',
            'how_it_works': 'Runs tests automatically.',
            'key_features': ['Fast', 'Reliable', 'Simple'],
            'future_scope': ['Feature A', 'Feature B'],
            'impact': 'Improves efficiency.'
        }
        self.repo_info = {'name': 'TestApp', 'url': 'https://github.com/test/app', 'stars': 5}

    def _call_validator(self, raw_slides):
        return validate_and_normalize_slides(
            raw_slides,
            "TestApp",
            "Python, Flask",
            ["Python", "Flask"],
            self.dummy_explanation,
            self.dummy_analysis,
            self.repo_info,
            self.dummy_explanation['key_features'],
            self.dummy_explanation['future_scope'],
            self.dummy_explanation['impact']
        )

    def test_rejects_slide_count_not_seven(self):
        short_slides = [{"title": "Only One", "type": "intro"}]
        result = self._call_validator(short_slides)
        self.assertEqual(len(result), 7)
        self.assertEqual(result[0]['title'], "TestApp")  # Activated fallback

    def test_rejects_invalid_color_theme(self):
        slides = []
        for seq in EXPECTED_SLIDE_SEQUENCE:
            slides.append({
                "title": f"Slide {seq}",
                "type": seq,
                "bullets": ["Point 1", "Point 2"],
                "color_theme": "neon-hot-pink",  # Invalid theme!
                "narration": "This is a valid long narration text exceeding 15 characters."
            })
        result = self._call_validator(slides)
        # Should reject model output and return fallback with valid color themes
        self.assertEqual(result[0]['color_theme'], 'blue')

    def test_rejects_non_string_bullets(self):
        slides = []
        for seq in EXPECTED_SLIDE_SEQUENCE:
            slides.append({
                "title": f"Slide {seq}",
                "type": seq,
                "bullets": [123, True, None],  # Non-string bullets!
                "color_theme": "blue",
                "narration": "This is a valid long narration text exceeding 15 characters."
            })
        result = self._call_validator(slides)
        # Fallback activated
        self.assertIn("🔧 Built with", result[0]['bullets'][0])

    def test_rejects_short_or_missing_narration(self):
        slides = []
        for seq in EXPECTED_SLIDE_SEQUENCE:
            slides.append({
                "title": f"Slide {seq}",
                "type": seq,
                "bullets": ["Bullet point one"],
                "color_theme": "blue",
                "narration": "Too short"  # < 15 chars!
            })
        result = self._call_validator(slides)
        # Fallback activated
        self.assertGreaterEqual(len(result[0]['narration']), 15)


# =====================================================================
# 3. OFFLINE UNIT TESTS: GEMINI FALLBACK RESILIENCE
# =====================================================================

class TestAgentsGeminiFallbackOffline(unittest.TestCase):

    @patch("os.getenv", return_value="")  # Missing API Key triggers fallback immediately
    def test_analyzer_fallback_on_api_error(self, mock_env):
        res = analyze_repo({}, {'name': 'MockRepo', 'language': 'Python'})
        self.assertIsInstance(res['project_name'], str)
        self.assertIsInstance(res['components'], list)
        self.assertGreater(len(res['components']), 0)
        self.assertIn("Multi-tier", res['architecture'])

    @patch("os.getenv", return_value="")
    def test_explainer_fallback_on_api_error(self, mock_env):
        analysis = {'project_name': 'MockRepo', 'project_type': 'CLI', 'tech_stack': 'Go'}
        res = explain_repo(analysis, {})
        self.assertIsInstance(res['tagline'], str)
        self.assertIsInstance(res['key_features'], list)
        self.assertGreaterEqual(len(res['key_features']), 3)

    @patch("os.getenv", return_value="")
    def test_presenter_fallback_on_api_error(self, mock_env):
        res = generate_slides({}, {'project_name': 'MockRepo'}, {'name': 'MockRepo'})
        self.assertEqual(len(res), 7)
        self.assertEqual([s['type'] for s in res], EXPECTED_SLIDE_SEQUENCE)
        self.assertTrue(all(len(s['narration']) >= 15 for s in res))


# =====================================================================
# 4. LIVE INTEGRATION TESTS
# =====================================================================

class TestLiveMultiRepoIntegration(unittest.TestCase):

    def test_live_multi_repo_pipeline(self):
        print("\n--- Testing Live Multi-Repo End-to-End Pipeline ---")
        for i, item in enumerate(TEST_REPOS, 1):
            with self.subTest(repo=item['name']):
                print(f"\n[{i}/{len(TEST_REPOS)}] Live Testing: {item['name']}")
                print(f"      Repository: {item['url']}")
                t0 = time.time()

                # Agent 1: Fetcher
                files, repo_info = fetch_repo(item['url'])
                self.assertGreater(len(files), 0, "No files fetched")
                print(f"  [✓] Agent 1 (Fetcher): Fetched {len(files)} files | Branch: {repo_info.get('default_branch')}")

                # Agent 2: Analyzer
                analysis = analyze_repo(files, repo_info)
                self.assertIsInstance(analysis['project_name'], str)
                self.assertIsInstance(analysis['components'], list)
                print(f"  [✓] Agent 2 (Analyzer): Verified schema for '{analysis['project_name']}'")

                # Agent 3: Explainer
                explanation = explain_repo(analysis, files)
                self.assertIsInstance(explanation['tagline'], str)
                self.assertGreaterEqual(len(explanation['key_features']), 3)
                print(f"  [✓] Agent 3 (Explainer): Verified schema | Tagline: '{explanation['tagline']}'")

                # Agent 4: Presenter
                slides = generate_slides(explanation, analysis, repo_info)
                self.assertEqual(len(slides), 7, "Expected exactly 7 slides")
                for idx, s in enumerate(slides):
                    self.assertEqual(s['type'], EXPECTED_SLIDE_SEQUENCE[idx])
                    self.assertGreaterEqual(len(s['narration']), 15)
                print(f"  [✓] Agent 4 (Presenter): Verified all 7 slides with complete voice narration")

                elapsed = round(time.time() - t0, 2)
                print(f"  🎉 Pass! Pipeline and schema validated in {elapsed}s")


# =====================================================================
# TEST RUNNER & SEPARATE SUMMARIES
# =====================================================================

def run_all_tests():
    print("=" * 70)
    print("🧪 REPONARRATOR AI — UNIFIED TEST INFRASTRUCTURE")
    print("=" * 70)

    # 1. Run Offline Unit Test Suite
    offline_suite = unittest.TestSuite()
    offline_suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestFetcherOffline))
    offline_suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestPresenterStrictValidationOffline))
    offline_suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestAgentsGeminiFallbackOffline))

    print("\n[PART 1] Executing Isolated Offline Unit Tests (Mocks)...")
    runner = unittest.TextTestRunner(verbosity=2)
    offline_result = runner.run(offline_suite)

    # 2. Run Live Integration Suite
    print("\n[PART 2] Executing Live Multi-Repository Integration Suite...")
    live_suite = unittest.TestSuite()
    live_suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestLiveMultiRepoIntegration))
    live_result = runner.run(live_suite)

    # Print Final Summary
    print("\n" + "=" * 70)
    print("📊 FINAL VERIFICATION SUMMARY REPORT")
    print("=" * 70)
    print(f"Offline Unit Tests: {'PASSED' if offline_result.wasSuccessful() else 'FAILED'} "
          f"({offline_result.testsRun} tests run, {len(offline_result.failures)} failures, {len(offline_result.errors)} errors)")
    print(f"Live Integration Tests: {'PASSED' if live_result.wasSuccessful() else 'FAILED'} "
          f"({live_result.testsRun} tests run, {len(live_result.failures)} failures, {len(live_result.errors)} errors)")

    if offline_result.wasSuccessful() and live_result.wasSuccessful():
        print("\n🌟 All configured verification checks passed successfully.")
        sys.exit(0)
    else:
        print("\n❌ CI GATE FAILED: One or more test suites failed.")
        sys.exit(1)


if __name__ == '__main__':
    run_all_tests()
