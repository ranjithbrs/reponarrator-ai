/* RepoNarrator AI — Frontend Logic
 * Handles: URL input, SSE streaming, agent animations, slide handoff
 */

// ── Helpers ──────────────────────────────────────────────────────────────────
function fillExample(url) {
  document.getElementById('repoUrl').value = url;
  document.getElementById('repoUrl').focus();
}

function showError(msg) {
  const toast = document.getElementById('errorToast');
  document.getElementById('errorMsg').textContent = msg;
  toast.style.display = 'flex';
  setTimeout(() => { toast.style.display = 'none'; }, 6000);
}

// ── Agent status update ───────────────────────────────────────────────────────
function setAgentActive(n) {
  const card = document.getElementById('agent' + n);
  if (card) card.classList.add('active');
}

function setAgentDone(n, statusText) {
  const card   = document.getElementById('agent' + n);
  const badge  = document.getElementById('badge' + n);
  const status = document.getElementById('status' + n);
  if (card)   { card.classList.remove('active'); card.classList.add('done'); }
  if (badge)  badge.textContent = '✅';
  if (status) status.textContent = statusText;
}

function setAgentStatus(n, statusText) {
  const el = document.getElementById('status' + n);
  if (el) el.textContent = statusText;
}

// ── Main analysis flow ────────────────────────────────────────────────────────
function startAnalysis() {
  const url = document.getElementById('repoUrl').value.trim();
  if (!url) {
    showError('Please enter a GitHub repository URL');
    return;
  }
  if (!url.includes('github.com')) {
    showError('Please enter a valid GitHub URL (e.g. https://github.com/owner/repo)');
    return;
  }

  // UI: Switch views
  document.getElementById('hero').style.display = 'none';
  document.getElementById('featuresSection').style.display = 'none';
  document.getElementById('pipelineSection').style.display = 'block';

  // Disable button
  const btn = document.getElementById('analyzeBtn');
  btn.disabled = true;
  document.getElementById('btnText').innerHTML = '<span class="spinner"></span> Analyzing...';

  // Show pipeline sub-text
  document.getElementById('pipelineSub').textContent = url;

  // Reset agent cards
  [1, 2, 3, 4].forEach(n => {
    const card = document.getElementById('agent' + n);
    const badge = document.getElementById('badge' + n);
    const status = document.getElementById('status' + n);
    if (card)   { card.classList.remove('active', 'done'); }
    if (badge)  badge.textContent = '⏳';
    if (status) status.textContent = 'Waiting...';
  });

  // Start SSE stream
  const evtSource = new EventSource(`/analyze?url=${encodeURIComponent(url)}`);

  evtSource.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.error) {
      evtSource.close();
      showError(data.error);
      resetUI();
      return;
    }

    // Agent progress updates
    if (data.agent) {
      if (!data.done) {
        setAgentActive(data.agent);
        setAgentStatus(data.agent, data.status);
      } else {
        setAgentDone(data.agent, data.status);
      }
    }

    // All done — go to presentation
    if (data.complete && data.slides) {
      evtSource.close();

      // Store in both localStorage and sessionStorage for bulletproof persistence
      localStorage.setItem('reponarrator_slides', JSON.stringify(data.slides));
      localStorage.setItem('reponarrator_info',   JSON.stringify(data.repo_info || {}));
      sessionStorage.setItem('reponarrator_slides', JSON.stringify(data.slides));
      sessionStorage.setItem('reponarrator_info',   JSON.stringify(data.repo_info || {}));

      // Show launch card immediately
      const launchCard = document.getElementById('launchCard');
      if (launchCard) {
        launchCard.style.display = 'block';
      }

      // Navigate within 600ms
      setTimeout(() => {
        window.location.href = '/presentation';
      }, 700);
    }
  };

  evtSource.onerror = () => {
    evtSource.close();
    showError('Connection error. Please try again.');
    resetUI();
  };
}

function resetUI() {
  const btn = document.getElementById('analyzeBtn');
  btn.disabled = false;
  document.getElementById('btnText').textContent = 'Analyze →';
  document.getElementById('pipelineSection').style.display = 'none';
  document.getElementById('hero').style.display = 'flex';
  document.getElementById('featuresSection').style.display = 'block';
}

// ── Enter key support ────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('repoUrl');
  if (input) {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') startAnalysis();
    });
  }
});
