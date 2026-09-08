# 🤖 RepoNarrator AI — Multi-Agent GitHub Presentation Generator

[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![AI: Google Gemini 2.0](https://img.shields.io/badge/AI-Gemini%202.0%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![Architecture: Multi--Agent](https://img.shields.io/badge/Architecture-Multi--Agent%20Pipeline-orange?style=for-the-badge)](agents/)
[![Realtime: Server--Sent Events](https://img.shields.io/badge/Streaming-Server--Sent%20Events%20(SSE)-success?style=for-the-badge)](app.py)
[![Presentation: Reveal.js](https://img.shields.io/badge/Slides-Reveal.js%20Engine-E44D26?style=for-the-badge&logo=html5&logoColor=white)](https://revealjs.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)](LICENSE)

> Transform any public GitHub repository into an executive-ready, interactive slide presentation in seconds using an autonomous 4-agent pipeline powered by Google Gemini 2.0 Flash and Server-Sent Events (SSE).

---

## 📑 Table of Contents
- [Multi-Agent Architecture & Sequence](#-multi-agent-architecture--sequence)
- [Agent Decomposition](#-agent-decomposition)
- [Key Technical Highlights](#-key-technical-highlights)
- [Interactive Demonstration Workflow](#-interactive-demonstration-workflow)
- [Repository Structure](#-repository-structure)
- [Local Development Setup](#-local-development-setup)
- [Author & Connect](#-author)
- [License](#-license)

---

## 📐 Multi-Agent Architecture & Sequence

The application choreographs four specialized AI agents connected via real-time **Server-Sent Events (SSE)**. State and artifacts pass downstream sequentially while streaming live progress directly to the browser UI:

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 Developer / Presenter
    participant UI as 🖥️ Web Client (SSE Listener)
    participant Server as ⚙️ Flask Controller (/analyze)
    participant Agent1 as 🔍 Agent 1: Fetcher
    participant Agent2 as 🧠 Agent 2: Analyzer (Gemini)
    participant Agent3 as 💬 Agent 3: Explainer (Gemini)
    participant Agent4 as 🎨 Agent 4: Presenter (Gemini)
    participant Slides as 📊 Presentation View (Reveal.js)

    User->>UI: Paste GitHub Repository URL & Click "Analyze"
    UI->>Server: GET /analyze?url={repo_url} (EventStream)
    
    Server->>Agent1: fetch_repo(repo_url)
    Agent1->>Agent1: Query GitHub REST API & filter binaries/dependencies
    Agent1-->>Server: Return {files, repo_info}
    Server-->>UI: event: Agent 1 Complete (Fetched N files)

    Server->>Agent2: analyze_repo(files, repo_info)
    Agent2->>Agent2: Gemini 2.0 Flash infers architecture, tech stack & patterns
    Agent2-->>Server: Return {tech_stack, architecture, components}
    Server-->>UI: event: Agent 2 Complete (Detected stack)

    Server->>Agent3: explain_repo(analysis, files)
    Agent3->>Agent3: Gemini 2.0 Flash synthesizes problem statement, solution & impact
    Agent3-->>Server: Return {problem, solution, key_features, impact}
    Server-->>UI: event: Agent 3 Complete (Explanation ready)

    Server->>Agent4: generate_slides(explanation, analysis, repo_info)
    Agent4->>Agent4: Synthesizes structured JSON into Reveal.js slide deck
    Agent4-->>Server: Return {slides_payload}
    Server-->>UI: event: Complete & Cache presentation payload
    
    UI->>Slides: Automatically launch presentation tab
    Slides-->>User: Interactive Reveal.js presentation with keyboard controls
```

---

## 🤖 Agent Decomposition

| Agent | Core Responsibility | Inputs | Outputs | AI Engine / Tool |
| :--- | :--- | :--- | :--- | :--- |
| **Agent 1: Fetcher** | Connects to GitHub REST API, parses repository trees, prioritizes source and configuration files, and filters binaries / build artifacts. | GitHub Repository URL | Manifest of key code files & repo metadata | GitHub API v3 / Python Requests |
| **Agent 2: Analyzer** | Inspects project directory hierarchies, package manifests, and code files to identify architecture patterns (MVC, Microservices, Event-Driven) and dependencies. | Filtered code files & metadata | Technical profile (languages, frameworks, DBs, design patterns) | Google Gemini 2.0 Flash |
| **Agent 3: Explainer** | Distills complex technical implementations into executive value propositions, problem definitions, architectural advantages, and real-world impact. | Technical profile & key files | Structured business & technical narrative | Google Gemini 2.0 Flash |
| **Agent 4: Presenter** | Transforms narrative points into structured presentation sections, speaker notes, and interactive Reveal.js slides. | Technical narrative & profile | Validated Reveal.js slide deck schema | Google Gemini 2.0 Flash + Reveal.js |

---

## ✨ Key Technical Highlights

1. **Autonomous Agentic Pipeline**:
   - Sequential multi-agent workflow where each agent operates with focused system instructions and specialized output schemas.
   - Graceful fallback routines for large codebases (context truncation, priority heuristics).

2. **Real-time Observability via Server-Sent Events (SSE)**:
   - Utilizes `text/event-stream` to establish a persistent unidirectional pipeline from the Python server to the frontend.
   - Eliminates polling latency while providing step-by-step transparency into agent thought processes and status.

3. **Reveal.js Presentation Engine**:
   - Generates interactive, accessible HTML5 slides with smooth 2D transition animations.
   - Full keyboard navigation support (<kbd>→</kbd>, <kbd>←</kbd>, <kbd>Space</kbd>, <kbd>Esc</kbd> for slide overview).
   - Embedded speaker notes and responsive layout for widescreen monitors and projectors.

4. **Zero-Hardcoding Configuration**:
   - Environment-driven API key management supporting both local `.env` and production PaaS environments.

---

## 🎯 Interactive Demonstration Workflow

1. **Launch**: Start the application and visit `http://127.0.0.1:5000`.
2. **Select Target Repository**: Click one of the quick chips or input any public GitHub URL (e.g. `https://github.com/ranjithbrs/secure-ai-journal-app`).
3. **Trigger Pipeline**: Click **Analyze →**.
4. **Live Agent Activity**: Observe the 4-agent status cards illuminate in real time:
   - 🔍 *Fetcher: Fetching repository tree and manifests...*
   - 🧠 *Analyzer: Identifying tech stack and architectural design...*
   - 💬 *Explainer: Distilling engineering impact and problem statement...*
   - 🎨 *Presenter: Compiling Reveal.js slide deck...*
5. **Interactive Deck**: A presentation window immediately launches, ready for live stakeholder presentations or technical interviews.

---

## 📁 Repository Structure

```text
reponarrator-ai/
├── app.py                      # Flask backend, SSE event streaming route & view controllers
├── Procfile                    # Production Gunicorn process manager definition
├── requirements.txt            # Python dependencies (Flask, google-genai, requests)
├── .env.example                # Template for Gemini API key configuration
├── README.md                   # Comprehensive project documentation
├── agents/
│   ├── fetcher.py              # Agent 1: GitHub API tree traversal & file filter
│   ├── analyzer.py             # Agent 2: Architecture & technology inference
│   ├── explainer.py            # Agent 3: Narrative & technical synthesis
│   └── presenter.py            # Agent 4: Reveal.js slide generation
├── static/
│   ├── css/                    # Dark glassmorphic design system
│   └── js/                     # SSE client listener & dynamic UI renderer
└── templates/
    ├── index.html              # Main multi-agent analysis dashboard
    └── presentation.html       # Full-screen Reveal.js presentation canvas
```

---

## 🚀 Local Development Setup

### Prerequisites
- Python 3.10 or higher installed.
- A **Google Gemini API Key** (obtain free from [Google AI Studio](https://aistudio.google.com/)).

### 1. Clone the Repository
```bash
git clone https://github.com/ranjithbrs/reponarrator-ai.git
cd reponarrator-ai
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the root folder:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Run the Application
```bash
python app.py
```
Open your browser at `http://127.0.0.1:5000`.

---

## 👨‍💻 Author

**Ranjith B**  
🎓 *B.Tech Computer Science & Business Systems (CSBS)*  
🏛️ *Nehru Institute of Engineering and Technology, Coimbatore*  

- 💼 **LinkedIn**: [linkedin.com/in/ranjith-b-85907831a](https://linkedin.com/in/ranjith-b-85907831a)  
- 🐙 **GitHub**: [github.com/ranjithbrs](https://github.com/ranjithbrs)  
- 🌐 **Portfolio**: [ranjithbrs.github.io/portfolio](https://ranjithbrs.github.io/portfolio/)  
- 📧 **Email**: ranjithb2k06@gmail.com  

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
