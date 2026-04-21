// ── SSN formatter ─────────────────────────────────────────────────────────
function formatSSN(input) {
    let v = input.value.replace(/\D/g, '').slice(0, 9);
    if (v.length > 5) {
        v = v.slice(0,3) + '-' + v.slice(3,5) + '-' + v.slice(5);
    } else if (v.length > 3) {
        v = v.slice(0,3) + '-' + v.slice(3);
    }
    input.value = v;
}

// ── Credit card formatter ──────────────────────────────────────────────────
function formatCard(input) {
    let v = input.value.replace(/\D/g, '').slice(0, 16);
    v = v.match(/.{1,4}/g)?.join(' ') || v;
    input.value = v;
}

// ── Expiry formatter ───────────────────────────────────────────────────────
function formatExpiry(input) {
    let v = input.value.replace(/\D/g, '').slice(0, 4);
    if (v.length > 2) {
        v = v.slice(0,2) + '/' + v.slice(2);
    }
    input.value = v;
}

// ── Routing number validator ───────────────────────────────────────────────
function validateRouting(input) {
    input.value = input.value.replace(/\D/g, '').slice(0, 9);
}

// ── Phone formatter ────────────────────────────────────────────────────────
function formatPhone(input) {
    let v = input.value.replace(/\D/g, '').slice(0, 10);
    if (v.length > 6) {
        v = '(' + v.slice(0,3) + ') ' + v.slice(3,6) + '-' + v.slice(6);
    } else if (v.length > 3) {
        v = '(' + v.slice(0,3) + ') ' + v.slice(3);
    }
    input.value = v;
}

// ── Attach formatters on DOMContentLoaded ─────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
    const ssn = document.getElementById('ssn');
    if (ssn) ssn.addEventListener('input', () => formatSSN(ssn));

    const card = document.getElementById('card_number');
    if (card) card.addEventListener('input', () => formatCard(card));

    const expiry = document.getElementById('card_expiry');
    if (expiry) expiry.addEventListener('input', () => formatExpiry(expiry));

    const routing = document.getElementById('routing_number');
    if (routing) routing.addEventListener('input', () => validateRouting(routing));

    const phone = document.getElementById('phone');
    if (phone) phone.addEventListener('input', () => formatPhone(phone));

    // ── Countdown timer (step 4 payment page) ─────────────────────────────
    const timerEl = document.getElementById('countdown-timer');
    if (timerEl) {
        let seconds = 10 * 60; // 10 minutes
        const tick = setInterval(function () {
            seconds--;
            if (seconds <= 0) {
                clearInterval(tick);
                timerEl.textContent = 'EXPIRED';
                timerEl.style.color = '#d62d20';
                return;
            }
            const m = Math.floor(seconds / 60);
            const s = seconds % 60;
            timerEl.textContent = m + ':' + String(s).padStart(2, '0');
            if (seconds <= 60) {
                timerEl.style.color = '#d62d20';
            }
        }, 1000);
    }

    // ── Form validation ────────────────────────────────────────────────────
    const forms = document.querySelectorAll('form.validated');
    forms.forEach(function (form) {
        form.addEventListener('submit', function (e) {
            let valid = true;
            form.querySelectorAll('[required]').forEach(function (field) {
                if (!field.value.trim()) {
                    field.classList.add('error');
                    valid = false;
                } else {
                    field.classList.remove('error');
                }
            });
            if (!valid) {
                e.preventDefault();
                const first = form.querySelector('.error');
                if (first) first.focus();
            }
        });
    });
});
