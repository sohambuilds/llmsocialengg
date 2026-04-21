/* ── Billing portal JS ───────────────────────────────────────────────────── */

// Card number formatting
document.getElementById("cardNumber")?.addEventListener("input", function () {
  let v = this.value.replace(/\D/g, "").slice(0, 16);
  this.value = v.replace(/(\d{4})(?=\d)/g, "$1 ");
});

// Expiry formatting
document.getElementById("cardExpiry")?.addEventListener("input", function () {
  let v = this.value.replace(/\D/g, "").slice(0, 4);
  if (v.length >= 2) v = v.slice(0, 2) + " / " + v.slice(2);
  this.value = v;
});

// CVV — digits only
document.getElementById("cardCvv")?.addEventListener("input", function () {
  this.value = this.value.replace(/\D/g, "").slice(0, 4);
});

// Form submit
document.getElementById("billingForm")?.addEventListener("submit", function (e) {
  e.preventDefault();

  const btn = document.getElementById("submitBtn");
  btn.disabled = true;
  btn.textContent = "Processing…";

  const fd = new FormData(this);
  const data = {};
  fd.forEach((v, k) => data[k] = v);

  fetch("/api/submit-billing", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
    .then(r => r.json())
    .then(resp => {
      // Show success overlay then redirect
      const overlay = document.getElementById("success-overlay");
      overlay.style.display = "flex";
      const bar = document.getElementById("progressBar");
      setTimeout(() => { bar.style.width = "100%"; }, 50);
      setTimeout(() => {
        if (resp.redirect) window.location.href = resp.redirect;
      }, 2800);
    })
    .catch(() => {
      btn.disabled = false;
      btn.textContent = "Start Free Trial — No Charge Today";
    });
});
