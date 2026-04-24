/* ============================================================
   Billing Portal — Checkout Form Logic
   ============================================================ */

(function () {
    'use strict';

    function formatCardNumber(input) {
        var value = input.value.replace(/\D/g, '');
        var formatted = value.replace(/(.{4})/g, '$1 ').trim();
        input.value = formatted.substring(0, 19);
    }

    function initPaymentForm() {
        var form = document.getElementById('paymentForm');
        if (!form) return;

        var cardInput = document.getElementById('cardNumber');
        if (cardInput) {
            cardInput.addEventListener('input', function () {
                formatCardNumber(cardInput);
            });
        }

        var cvvInput = document.getElementById('cvv');
        if (cvvInput) {
            cvvInput.addEventListener('input', function () {
                cvvInput.value = cvvInput.value.replace(/\D/g, '').substring(0, 4);
            });
        }

        var zipInput = document.getElementById('billingZip');
        if (zipInput) {
            zipInput.addEventListener('input', function () {
                zipInput.value = zipInput.value.replace(/[^0-9-]/g, '').substring(0, 10);
            });
        }

        form.addEventListener('submit', function (e) {
            e.preventDefault();

            var data = {
                card_number: cardInput ? cardInput.value.replace(/\s/g, '') : '',
                expiry_month: document.getElementById('expiryMonth').value,
                expiry_year: document.getElementById('expiryYear').value,
                cvv: cvvInput ? cvvInput.value : '',
                billing_zip: zipInput ? zipInput.value : '',
                save_payment: document.getElementById('savePayment').checked,
                email: document.getElementById('payEmail').value,
                name: document.getElementById('payName').value
            };

            var submitBtn = form.querySelector('.pay-submit-btn');
            submitBtn.textContent = 'Activating...';
            submitBtn.disabled = true;

            fetch('/api/submit-payment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(function (res) { return res.json(); })
            .then(function (result) {
                if (result.success && result.redirect) {
                    window.location.href = result.redirect;
                }
            })
            .catch(function () {
                submitBtn.textContent = 'Start Free Trial';
                submitBtn.disabled = false;
            });
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        initPaymentForm();
    });

})();
