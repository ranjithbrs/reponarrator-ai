"""
Agent 1 — Fetcher
Fetches and prioritizes source code files and manifests from GitHub repositories.
Features:
1. Dynamic default_branch discovery via repository metadata.
2. Structured exceptions for 401 (Auth), 403 (Rate Limit/Forbidden), 404 (Not Found/Private).
3. Resilient zipball extraction with archive download byte caps (max 30MB) and file size safety.
4. Token-aware GitHub REST API tree fallback.
"""

import os
import requests
import base64
import re
import io
import zipfile
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

MAX_FILES = 25
MAX_FILE_SIZE = 50000        # 50KB per individual file
MAX_ZIPBALL_SIZE = 30000000  # 30MB max compressed zipball download

SKIP_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
    '.pdf', '.zip', '.exe', '.mp4', '.mp3', '.woff',
    '.woff2', '.ttf', '.eot', '.otf', '.lock', '.class',
    '.jar', '.pyc', '.tar', '.gz'
}

SKIP_DIRS = {
    'node_modules', '.git', 'dist', 'build', 'target',
    '__pycache__', '.venv', 'venv', '.next', 'coverage',
    '.idea', '.vscode'
}

PRIORITY_FILES = {
    'readme.md', 'readme.txt', 'app.py', 'main.py',
    'index.js', 'index.ts', 'package.json', 'pom.xml',
    'requirements.txt', 'application.properties', 'settings.py',
    'dockerfile', 'docker-compose.yml'
}


class GitHubFetchError(Exception):
    """Base exception for GitHub fetching errors."""
    pass

class GitHubAuthError(GitHubFetchError):
    """Raised when GITHUB_TOKEN is invalid or expired (HTTP 401)."""
    pass

class GitHubRateLimitError(GitHubFetchError):
    """Raised when GitHub API rate limit is exceeded (HTTP 403 rate-limited)."""
    pass

class GitHubAccessForbiddenError(GitHubFetchError):
    """Raised when access is forbidden by repository permissions or organization policy."""
    pass

class GitHubNotFoundError(GitHubFetchError):
    """Raised when a repository is not found or is private (HTTP 404)."""
    pass


def get_github_headers():
    """Build request headers, attaching GITHUB_TOKEN if present."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) RepoNarrator-AI',
        'Accept': 'application/vnd.github.v3+json'
    }
    token = os.getenv('GITHUB_TOKEN')
    if token and token.strip():
        headers['Authorization'] = f"token {token.strip()}"
    return headers


def parse_github_url(url):
    """Extract owner and repo name from any GitHub URL format."""
    if not url or not isinstance(url, str):
        raise ValueError("GitHub URL must be a non-empty string.")
    clean_url = url.strip().rstrip('/')
    match = re.search(r'github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/|$)', clean_url)
    if match:
        return match.group(1), match.group(2)
    raise ValueError(f"Invalid GitHub URL: '{url}'. Expected format: https://github.com/owner/repo")


def fetch_repo_via_zip(owner, repo, branches):
    """
    Download and extract repository files using GitHub's zipball archive endpoint.
    Safely enforces archive download size caps and file filters.
    """
    files = {}
    token = os.getenv('GITHUB_TOKEN')
    req_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) RepoNarrator-AI'}
    if token and token.strip():
        req_headers['Authorization'] = f"token {token.strip()}"

    for branch in branches:
        zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
        try:
            req = urllib.request.Request(zip_url, headers=req_headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    # Enforce download size cap
                    content_length = resp.headers.get('Content-Length')
                    if content_length and int(content_length) > MAX_ZIPBALL_SIZE:
                        print(f"Zipball exceeds maximum allowed size ({content_length} bytes). Aborting zip extraction.")
                        break

                    zip_data = resp.read(MAX_ZIPBALL_SIZE + 1)
                    if len(zip_data) > MAX_ZIPBALL_SIZE:
                        print(f"Zipball stream exceeded {MAX_ZIPBALL_SIZE} bytes. Aborting zip extraction.")
                        break

                    with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
                        namelist = z.namelist()

                        def sort_key(name):
                            basename = name.split('/')[-1].lower()
                            return (0 if basename in PRIORITY_FILES else 1, name)

                        namelist.sort(key=sort_key)

                        for member in namelist:
                            if len(files) >= MAX_FILES:
                                break
                            if member.endswith('/'):
                                continue
                            parts = member.split('/')[1:]  # Strip root archive folder
                            if not parts:
                                continue
                            if any(p in SKIP_DIRS for p in parts):
                                continue
                            rel_path = '/'.join(parts)
                            ext = ('.' + rel_path.rsplit('.', 1)[-1]).lower() if '.' in rel_path else ''
                            if ext in SKIP_EXTENSIONS:
                                continue
                            info = z.getinfo(member)
                            if info.file_size > MAX_FILE_SIZE:
                                continue
                            try:
                                content = z.read(member).decode('utf-8', errors='replace')
                                files[rel_path] = content
                            except Exception:
                                pass
                    if files:
                        return files
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Branch might not exist, proceed to test next branch
                continue
            elif e.code == 401:
                raise GitHubAuthError("GitHub authentication failed. Check your GITHUB_TOKEN.")
            elif e.code == 403:
                raise GitHubAccessForbiddenError("Access to repository archive is forbidden or rate-limited.")
        except Exception:
            continue

    return files


def fetch_repo(repo_url):
    """
    Fetch repository metadata and source files with comprehensive error handling.
    Returns: (files_dict, repo_info_dict)
    """
    owner, repo = parse_github_url(repo_url)

    repo_info = {
        'name': repo,
        'description': '',
        'language': '',
        'stars': 0,
        'url': repo_url,
        'owner': owner,
        'topics': [],
        'homepage': '',
        'default_branch': 'main'
    }

    headers = get_github_headers()
    branches_to_try = []

    # 1. Retrieve Repository Metadata first to determine default_branch and inspect HTTP status
    try:
        repo_api = f"https://api.github.com/repos/{owner}/{repo}"
        r = requests.get(repo_api, headers=headers, timeout=8)

        if r.status_code == 200:
            repo_data = r.json()
            default_branch = repo_data.get('default_branch', 'main')
            repo_info.update({
                'name': repo_data.get('name', repo),
                'description': repo_data.get('description', '') or '',
                'language': repo_data.get('language', '') or '',
                'stars': repo_data.get('stargazers_count', 0),
                'topics': repo_data.get('topics', []),
                'homepage': repo_data.get('homepage', '') or '',
                'default_branch': default_branch
            })
            branches_to_try.append(default_branch)

        elif r.status_code == 401:
            raise GitHubAuthError(f"Invalid or expired GITHUB_TOKEN provided for repository {owner}/{repo}.")

        elif r.status_code == 403:
            remaining = r.headers.get('X-RateLimit-Remaining')
            if remaining == '0':
                reset_time = r.headers.get('X-RateLimit-Reset', 'soon')
                raise GitHubRateLimitError(
                    f"GitHub API rate limit exceeded for {owner}/{repo}. (Resets at timestamp {reset_time}). "
                    "Configure a GITHUB_TOKEN in .env to lift limits to 5,000 requests/hour."
                )
            else:
                print(f"Warning: Access to repository metadata for {owner}/{repo} is forbidden (HTTP 403). Falling back to direct zip.")

        elif r.status_code == 404:
            raise GitHubNotFoundError(
                f"Repository '{owner}/{repo}' not found on GitHub (HTTP 404). "
                "Note: If this is a private repository, ensure GITHUB_TOKEN is configured with 'repo' scope."
            )
        else:
            print(f"Warning: GitHub API returned status {r.status_code}. Attempting direct zip extraction.")

    except requests.exceptions.Timeout:
        print(f"Warning: GitHub API connection timed out for {owner}/{repo}. Proceeding with fallback branches.")
    except (GitHubAuthError, GitHubRateLimitError, GitHubNotFoundError):
        raise
    except requests.exceptions.RequestException as e:
        print(f"Warning: Network error contacting GitHub API: {e}. Proceeding with zip extraction.")

    # Populate fallback candidate branches
    for fallback in ['main', 'master', 'dev', 'trunk']:
        if fallback not in branches_to_try:
            branches_to_try.append(fallback)

    # 2. Preferred Extraction: Fast Zipball extraction
    files = fetch_repo_via_zip(owner, repo, branches_to_try)

    # 3. Fallback: GitHub REST API Tree & Blobs
    if not files:
        tree_data = None
        for branch in branches_to_try:
            tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
            try:
                tr = requests.get(tree_url, headers=headers, timeout=8)
                if tr.status_code == 200:
                    tree_data = tr.json()
                    break
                elif tr.status_code == 403 and tr.headers.get('X-RateLimit-Remaining') == '0':
                    raise GitHubRateLimitError("GitHub API rate limit exceeded while querying repository tree.")
            except GitHubRateLimitError:
                raise
            except Exception:
                pass

        if tree_data:
            all_blobs = [item for item in tree_data.get('tree', []) if item.get('type') == 'blob']
            for item in all_blobs:
                if len(files) >= MAX_FILES:
                    break
                path = item['path']
                parts = path.split('/')
                if any(p in SKIP_DIRS for p in parts):
                    continue
                ext = ('.' + path.rsplit('.', 1)[-1]).lower() if '.' in path else ''
                if ext in SKIP_EXTENSIONS:
                    continue
                try:
                    content_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
                    cr = requests.get(content_url, headers=headers, timeout=6)
                    if cr.status_code == 200:
                        c_data = cr.json()
                        if c_data.get('encoding') == 'base64':
                            raw = base64.b64decode(c_data['content']).decode('utf-8', errors='replace')
                            if len(raw) <= MAX_FILE_SIZE:
                                files[path] = raw
                except Exception:
                    pass

    if not files:
        raise GitHubFetchError(
            f"Unable to read repository files for '{owner}/{repo}'. "
            f"Checked branches: {', '.join(branches_to_try)}. "
            "Please verify that the repository is public or your GITHUB_TOKEN has access."
        )

    return files, repo_info
