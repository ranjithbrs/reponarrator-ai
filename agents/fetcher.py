"""
Agent 1 — Fetcher
Fetches all source code files from a public GitHub repository.
Supports:
1. Direct Zipball extraction (no GitHub API rate limits, ultra-fast)
2. GitHub REST API fallback
"""

import os
import requests
import base64
import re
import io
import zipfile
import urllib.request
from dotenv import load_dotenv

load_dotenv()

MAX_FILES = 25
MAX_FILE_SIZE = 50000  # 50KB per file

SKIP_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
    '.pdf', '.zip', '.exe', '.mp4', '.mp3', '.woff',
    '.woff2', '.ttf', '.eot', '.otf', '.lock', '.class',
    '.jar', '.pyc'
}

SKIP_DIRS = {
    'node_modules', '.git', 'dist', 'build', 'target',
    '__pycache__', '.venv', 'venv', '.next', 'coverage',
    '.idea', '.vscode'
}

PRIORITY_FILES = {
    'readme.md', 'readme.txt', 'app.py', 'main.py',
    'index.js', 'index.ts', 'package.json', 'pom.xml',
    'requirements.txt', 'application.properties', 'settings.py'
}


def get_github_headers():
    """Build request headers, optionally attaching GITHUB_TOKEN for elevated rate limits."""
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
    url = url.strip().rstrip('/')
    match = re.search(r'github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/|$)', url)
    if match:
        return match.group(1), match.group(2)
    raise ValueError("Invalid GitHub URL. Example: https://github.com/owner/repo")


def fetch_repo_via_zip(owner, repo):
    """Download the public repo zip directly without any GitHub API rate limits."""
    files = {}
    headers = get_github_headers()
    token = os.getenv('GITHUB_TOKEN')
    
    # Try default branches and zip archive
    for branch in ['main', 'master']:
        zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
        try:
            req_headers = {'User-Agent': 'Mozilla/5.0'}
            if token and token.strip():
                req_headers['Authorization'] = f"token {token.strip()}"
            req = urllib.request.Request(zip_url, headers=req_headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    zip_data = resp.read()
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
                            parts = member.split('/')[1:] # drop top-level folder
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
        except Exception:
            continue
    return files


def fetch_repo(repo_url):
    """
    Fetch repository metadata and source files.
    Returns: (files_dict, repo_info_dict)
    """
    owner, repo = parse_github_url(repo_url)

    # Basic repo info fallback
    repo_info = {
        'name': repo,
        'description': '',
        'language': '',
        'stars': 0,
        'url': repo_url,
        'owner': owner,
        'topics': [],
        'homepage': '',
    }

    # Attempt metadata from API (with token if configured)
    headers = get_github_headers()
    try:
        repo_api = f"https://api.github.com/repos/{owner}/{repo}"
        r = requests.get(repo_api, headers=headers, timeout=5)
        if r.status_code == 200:
            repo_data = r.json()
            repo_info.update({
                'name': repo_data.get('name', repo),
                'description': repo_data.get('description', ''),
                'language': repo_data.get('language', ''),
                'stars': repo_data.get('stargazers_count', 0),
                'topics': repo_data.get('topics', []),
                'homepage': repo_data.get('homepage', ''),
            })
        elif r.status_code == 403:
            print(f"Warning: GitHub API rate limited or forbidden for {owner}/{repo}. Falling back to zip extraction.")
        elif r.status_code == 404:
            raise Exception(f"Repository {owner}/{repo} not found on GitHub. Please check the URL.")
    except Exception as e:
        if "not found" in str(e).lower():
            raise e
        pass

    # Method 1: Fetch via GitHub public ZIP archive (never hits 60 req/hr rate limit)
    files = fetch_repo_via_zip(owner, repo)

    # Method 2: If ZIP extraction yielded nothing, try GitHub REST API
    if not files:
        tree_data = None
        for branch in ['main', 'master']:
            tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
            try:
                tr = requests.get(tree_url, headers=headers, timeout=8)
                if tr.status_code == 200:
                    tree_data = tr.json()
                    break
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
        raise Exception(f"Unable to read repository files for {owner}/{repo}. Please check if the repository is public or if branch is neither main nor master.")

    return files, repo_info
