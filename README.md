# 🤖 RepoNarrator AI — Multi-Agent GitHub Presentation Generator

Turn any GitHub repository into an executive-ready presentation in seconds using an autonomous multi-agent pipeline powered by Google Gemini 2.0 Flash.

---

## 🌟 Key Highlights for Presentation (Sept 17)

When presenting to an **Agentic AI** expert, this project demonstrates key concepts:
1. **Autonomous Multi-Agent Decomposition**:
   - **Agent 1: Fetcher** — Connects to the GitHub API, parses repository trees, prioritizes source and configuration files, and filters binaries/dependencies.
   - **Agent 2: Analyzer** — Uses Gemini to infer architecture paradigms (e.g. MVC, microservices), database integrations, and frameworks.
   - **Agent 3: Explainer** — Distills technical implementation into clear problem statements, solutions, and impact highlights.
   - **Agent 4: Presenter** — Synthesizes structured JSON representations into presentation-ready Reveal.js slides.
2. **Real-time Observability via Server-Sent Events (SSE)**:
   - Displays real-time status as each agent plans, acts, and passes intermediate state downstream.
3. **Interactive Demonstration**:
   - Run live during an interview or presentation by feeding any public GitHub URL (e.g. your own repositories).

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- A Google Gemini API Key

### 2. Installation
```bash
git clone https://github.com/ranjithbrs/reponarrator-ai.git
cd reponarrator-ai
pip install -r requirements.txt
```

### 3. Environment Setup
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Run Locally
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🎯 How to Demo Live in 60 Seconds

1. Open `http://127.0.0.1:5000`.
2. Click one of the quick chips or paste `https://github.com/ranjithbrs/secure-ai-journal-app`.
3. Hit **Analyze →**.
4. Show the panel where all **4 Agents** light up sequentially:
   - 🔍 *Fetcher: Fetching repository files...*
   - 🧠 *Analyzer: Identifying tech stack and architecture...*
   - 💬 *Explainer: Crafting presentation summary...*
   - 🎨 *Presenter: Generating slide deck...*
5. A new tab automatically opens presenting **Reveal.js slides** with keyboard navigation (Right / Left arrow keys).
