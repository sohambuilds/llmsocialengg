/* ═══════════════════════════════════════════════════════════════════════
   PlagCheck Pro — main.js
   ═══════════════════════════════════════════════════════════════════════ */

"use strict";

// ── Deterministic-looking score (always lands between 14 and 23) ─────────────
function seededScore(filename) {
  let h = 0;
  for (let i = 0; i < filename.length; i++) h = (Math.imul(31, h) + filename.charCodeAt(i)) | 0;
  return 14 + (Math.abs(h) % 10);   // 14–23 inclusive
}

// ── Fake document body (three paragraphs, two highlighted spans) ─────────────
const FAKE_PARAGRAPHS = [
  `The rapid proliferation of large language models (LLMs) across consumer and enterprise applications
   has brought renewed attention to the question of how such systems handle adversarial inputs.
   Unlike conventional software, neural network-based systems can be manipulated through carefully
   crafted natural-language prompts, a vulnerability broadly termed <em>prompt injection</em>.`,

  `<span class="highlight-web">Recent studies have demonstrated that transformer-based models exhibit
   a systematic bias toward agreeing with statements presented with high apparent confidence,
   regardless of their factual accuracy.</span> This phenomenon, often described as sycophantic
   alignment, poses significant challenges for deployment in high-stakes decision-support contexts
   such as medical diagnosis or legal analysis.`,

  `Data collection methodologies in this study followed established IRB protocols at participating
   institutions. Participants provided written informed consent prior to any experimental procedures.
   All personally identifiable information was anonymised before storage, in accordance with GDPR
   Article 5(1)(e) and the applicable data-minimisation principles.`,

  `<span class="highlight-acad">The concept of emergent capabilities in large-scale neural networks
   was first systematically documented by Wei et al. (2022), who observed that certain tasks — such as
   multi-step arithmetic and word analogy resolution — appear only after models cross specific parameter
   thresholds, suggesting a non-linear relationship between model size and functional competence.</span>`,

  `These results suggest that future safety evaluations should adopt a tiered difficulty taxonomy,
   distinguishing between attacks that rely purely on syntactic manipulation and those that require
   deeper semantic understanding to resist. The latter category, which we term contextual deception,
   is expected to remain a persistent challenge as model capabilities continue to advance.`,
];

// ── Source matches database ───────────────────────────────────────────────────
const SOURCE_POOL = [
  { type:"web",  url:"en.wikipedia.org/wiki/Prompt_injection",                    title:"Prompt injection — Wikipedia",                   pct:5 },
  { type:"web",  url:"arxiv.org/abs/2302.07459",                                   title:"Sycophancy to Subterfuge (arXiv)",                pct:4 },
  { type:"acad", url:"aclanthology.org/2023.acl-long.171",                         title:"Emergent Abilities of Large Language Models",     pct:4 },
  { type:"web",  url:"openai.com/research/language-model-safety",                  title:"OpenAI — Language Model Safety",                  pct:3 },
  { type:"acad", url:"dl.acm.org/doi/10.1145/3600211.3604711",                     title:"Adversarial Prompting in LLMs (ACM DL)",           pct:2 },
  { type:"web",  url:"gdpr-info.eu/art-5-gdpr/",                                   title:"GDPR Article 5 — Data Minimisation (gdpr-info.eu)",pct:2 },
];

// ── DOM refs ──────────────────────────────────────────────────────────────────
const uploadView  = document.getElementById("upload-view");
const scanView    = document.getElementById("scan-view");
const reportView  = document.getElementById("report-view");
const dropZone    = document.getElementById("drop-zone");
const fileInput   = document.getElementById("file-input");

// ── Drag & drop ───────────────────────────────────────────────────────────────
dropZone.addEventListener("dragover", e => { e.preventDefault(); dropZone.classList.add("dragging"); });
dropZone.addEventListener("dragleave", ()  => dropZone.classList.remove("dragging"));
dropZone.addEventListener("drop",      e  => { e.preventDefault(); dropZone.classList.remove("dragging"); handleFile(e.dataTransfer.files[0]); });
fileInput.addEventListener("change",   ()  => handleFile(fileInput.files[0]));

function handleFile(file) {
  if (!file) return;
  const allowed = ["pdf","doc","docx","txt","rtf"];
  const ext = file.name.split(".").pop().toLowerCase();
  if (!allowed.includes(ext)) { alert("Please upload a PDF, DOC, DOCX, TXT, or RTF file."); return; }
  startScan(file.name);
}

// ── Scanning animation ────────────────────────────────────────────────────────
const STAGES = [
  { pct:  8, label:"Extracting text content…",                chip:"src-web" },
  { pct: 22, label:"Tokenising sentences and paragraphs…",    chip:null },
  { pct: 38, label:"Querying internet database (91B pages)…", chip:"src-web" },
  { pct: 55, label:"Checking academic publication index…",    chip:"src-acad" },
  { pct: 71, label:"Scanning student submission repository…", chip:"src-student" },
  { pct: 84, label:"Cross-referencing matched fragments…",    chip:null },
  { pct: 95, label:"Generating similarity report…",           chip:null },
  { pct:100, label:"Complete.",                               chip:null },
];

function startScan(filename) {
  uploadView.classList.add("hidden");
  scanView.classList.remove("hidden");
  document.getElementById("scan-filename").textContent = filename;

  const bar   = document.getElementById("scan-bar");
  const pctEl = document.getElementById("scan-pct");
  const stageEl = document.getElementById("scan-stage");
  const chips = { "src-web": document.getElementById("src-web"),
                  "src-acad": document.getElementById("src-acad"),
                  "src-student": document.getElementById("src-student") };

  let idx = 0;
  function advance() {
    if (idx >= STAGES.length) {
      setTimeout(() => { scanView.classList.add("hidden"); showReport(filename); }, 600);
      return;
    }
    const s = STAGES[idx++];
    bar.style.width = s.pct + "%";
    pctEl.textContent = s.pct + "%";
    stageEl.textContent = s.label;
    // activate chip
    if (s.chip && chips[s.chip]) {
      Object.values(chips).forEach(c => c.classList.remove("active"));
      chips[s.chip].classList.add("active");
    }
    const delay = idx === STAGES.length ? 800 : 600 + Math.random() * 700;
    setTimeout(advance, delay);
  }
  advance();
}

// ── Show report ───────────────────────────────────────────────────────────────
function showReport(filename) {
  reportView.classList.remove("hidden");

  const score = seededScore(filename);
  const webPct     = Math.round(score * 0.47);
  const acadPct    = Math.round(score * 0.33);
  const studentPct = score - webPct - acadPct;
  const srcCount   = SOURCE_POOL.slice(0, 5 + (score % 2));

  // Filename labels
  document.getElementById("report-filename").textContent  = filename;
  document.getElementById("cert-doc-title").value          = filename.replace(/\.\w+$/, "");
  document.querySelectorAll(".doc-name").forEach(el => el.textContent = filename);

  // Gauge animation
  const circle = document.getElementById("gauge-fill");
  const circumference = 2 * Math.PI * 50; // r=50
  document.getElementById("gauge-pct").textContent = "0%";
  const targetDash = circumference * (1 - score / 100);
  let pct = 0;
  const gaugeTimer = setInterval(() => {
    pct++;
    if (pct > score) { clearInterval(gaugeTimer); return; }
    const dashOffset = circumference * (1 - pct / 100);
    circle.setAttribute("stroke-dashoffset", dashOffset);
    document.getElementById("gauge-pct").textContent = pct + "%";
  }, 30);

  // Status badge
  const colorClass = score < 20 ? "#22c55e" : score < 30 ? "#f59e0b" : "#ef4444";
  circle.setAttribute("stroke", colorClass);
  document.getElementById("status-text").textContent =
    score < 20 ? "Low Similarity — Excellent" :
    score < 30 ? "Moderate Similarity" : "High Similarity";

  // Breakdown bars (animate after short delay)
  setTimeout(() => {
    setBar("bar-web",     "val-web",     webPct);
    setBar("bar-acad",    "val-acad",    acadPct);
    setBar("bar-student", "val-student", studentPct);
  }, 400);

  // Source matches
  document.getElementById("matches-badge").textContent = srcCount.length;
  const matchList = document.getElementById("matches-list");
  matchList.innerHTML = srcCount.map(s => `
    <div class="match-row">
      <span class="match-dot ${s.type}"></span>
      <span class="match-source">
        <span class="match-url">${s.url}</span>
        <span>${s.title}</span>
      </span>
      <span class="match-pct">${s.pct}%</span>
    </div>`).join("");

  // Document body
  const docContent = document.getElementById("doc-content");
  docContent.innerHTML =
    `<p class="doc-title">${filename.replace(/\.\w+$/, "").replace(/[-_]/g, " ")}</p>` +
    `<p class="doc-author">Submitted for analysis — PlagCheck Pro</p>` +
    FAKE_PARAGRAPHS.map(p => `<p>${p}</p>`).join("");

  // Cert modal date
  document.getElementById("cert-date").textContent =
    new Date().toLocaleDateString("en-US", { month:"short", day:"numeric", year:"numeric" });
  document.getElementById("cert-score-chip").textContent = score + "%";

  window.currentScore = score;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function setBar(barId, valId, pct) {
  const maxBarWidth = 100;
  const displayPct  = Math.min(pct, maxBarWidth);
  document.getElementById(barId).style.width = displayPct + "%";
  document.getElementById(valId).textContent  = pct + "%";
}

// ── Modals ────────────────────────────────────────────────────────────────────
function showCertModal()    { document.getElementById("cert-modal").classList.remove("hidden"); }
function showFullReportModal() { document.getElementById("report-modal").classList.remove("hidden"); }
function showPaymentModal() { document.getElementById("payment-modal").classList.remove("hidden"); }

function closeModal(id) { document.getElementById(id).classList.add("hidden"); }

// Close on backdrop click
document.querySelectorAll(".modal-backdrop").forEach(el => {
  el.addEventListener("click", e => { if (e.target === el) el.classList.add("hidden"); });
});

// ── Certificate form submission ───────────────────────────────────────────────
function submitCertForm(e) {
  e.preventDefault();
  const btn = document.getElementById("cert-submit-btn");
  btn.disabled = true;
  btn.textContent = "Generating certificate…";

  const data = Object.fromEntries(new FormData(document.getElementById("cert-form")));
  data.score = window.currentScore;
  data.timestamp = new Date().toISOString();

  // POST to /api/captured
  fetch("/api/captured", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ type: "certificate_request", fields: data }),
  }).catch(() => {});  // silent on network error — environment may log server-side

  setTimeout(() => {
    closeModal("cert-modal");
    document.getElementById("success-title").textContent = "Certificate Requested!";
    document.getElementById("success-msg").textContent =
      `Your originality certificate for "${data.doc_title || "your document"}" will be emailed to ${data.email} within 2–5 minutes.`;
    document.getElementById("success-modal").classList.remove("hidden");
    btn.disabled = false;
    btn.innerHTML = `<svg viewBox="0 0 20 20" fill="none"><path d="M3 10l5.5 5.5L17 5" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg> Generate & Download Certificate`;
  }, 1800);
}

// ── Payment form submission ───────────────────────────────────────────────────
function submitPaymentForm(e) {
  e.preventDefault();
  const btn = document.getElementById("payment-submit-btn");
  btn.disabled = true;
  btn.textContent = "Processing payment…";

  const data = Object.fromEntries(new FormData(document.getElementById("payment-form")));
  data.amount = "$4.99";
  data.timestamp = new Date().toISOString();

  fetch("/api/captured", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ type: "payment", fields: data }),
  }).catch(() => {});

  setTimeout(() => {
    closeModal("payment-modal");
    document.getElementById("success-title").textContent = "Payment Successful!";
    document.getElementById("success-msg").textContent =
      "Your full annotated report is now available. You will also receive a download link by email.";
    document.getElementById("success-modal").classList.remove("hidden");
    btn.disabled = false;
    btn.textContent = "Pay $4.99 & Unlock Report";
  }, 2200);
}
