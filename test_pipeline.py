"""
Comprehensive Multi-Repo Pipeline Verification Script
Tests RepoNarrator AI agents across 3 different repository types:
1. Python/Flask Backend & Web App (CertValid)
2. Java / OOP Application (Online-Examination-System)
3. Full-Stack AI Project (secure-ai-journal-app)
"""

import sys
import os
import json
import time

# Ensure root dir is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.fetcher import fetch_repo
from agents.analyzer import analyze_repo
from agents.explainer import explain_repo
from agents.presenter import generate_slides

TEST_REPOS = [
    {
        "name": "Python / Flask Web App",
        "url": "https://github.com/ranjithbrs/CertValid"
    },
    {
        "name": "Java / OOP Academic System",
        "url": "https://github.com/ranjithbrs/Online-Examination-System"
    },
    {
        "name": "Full-Stack AI Project",
        "url": "https://github.com/ranjithbrs/secure-ai-journal-app"
    }
]

def run_tests():
    print("=" * 60)
    print("🧪 STARTING MULTI-REPO VERIFICATION SUITE")
    print("=" * 60)

    results = []

    for i, item in enumerate(TEST_REPOS, 1):
        print(f"\n[{i}/3] Testing: {item['name']}")
        print(f"      URL: {item['url']}")
        start_time = time.time()

        try:
            # Step 1: Agent 1 (Fetcher)
            files, repo_info = fetch_repo(item['url'])
            file_count = len(files)
            print(f"  [✓] Agent 1 (Fetcher): Fetched {file_count} files | Stars: {repo_info.get('stars', 0)}")
            assert file_count > 0, "No files fetched!"

            # Step 2: Agent 2 (Analyzer)
            analysis = analyze_repo(files, repo_info)
            project_name = analysis.get('project_name', 'Unknown')
            tech_stack = analysis.get('tech_stack', 'Unknown')
            print(f"  [✓] Agent 2 (Analyzer): Detected '{project_name}' | Stack: {tech_stack}")
            assert project_name, "Missing project name"
            assert tech_stack, "Missing tech stack"

            # Step 3: Agent 3 (Explainer)
            explanation = explain_repo(analysis, files)
            tagline = explanation.get('tagline', '')
            key_features = explanation.get('key_features', [])
            print(f"  [✓] Agent 3 (Explainer): Tagline: '{tagline}' | Features: {len(key_features)}")
            assert tagline, "Missing tagline"
            assert len(key_features) > 0, "No key features generated"

            # Step 4: Agent 4 (Presenter)
            slides = generate_slides(explanation, analysis, repo_info)
            print(f"  [✓] Agent 4 (Presenter): Generated {len(slides)} slides with voice narrations")
            assert len(slides) >= 5, f"Expected at least 5 slides, got {len(slides)}"
            
            # Check voice narration on slides
            has_narration = any(bool(s.get('narration')) for s in slides)
            assert has_narration, "Missing voice narration in slides!"

            elapsed = round(time.time() - start_time, 2)
            print(f"  🎉 Pass! Pipeline completed in {elapsed}s")
            results.append({"name": item['name'], "status": "PASSED", "time": elapsed})

        except Exception as e:
            elapsed = round(time.time() - start_time, 2)
            print(f"  ❌ Failed: {str(e)} ({elapsed}s)")
            results.append({"name": item['name'], "status": f"FAILED: {e}", "time": elapsed})

    print("\n" + "=" * 60)
    print("📊 VERIFICATION RESULTS SUMMARY")
    print("=" * 60)
    all_passed = True
    for r in results:
        status_icon = "✅" if r["status"] == "PASSED" else "❌"
        print(f"{status_icon} {r['name']}: {r['status']} ({r['time']}s)")
        if r["status"] != "PASSED":
            all_passed = False

    if all_passed:
        print("\n🌟 ALL MULTI-REPO TESTS PASSED! Pipeline is verified across languages & frameworks.")
    else:
        print("\n⚠️ Some tests encountered issues. Review log output above.")

if __name__ == '__main__':
    run_tests()
