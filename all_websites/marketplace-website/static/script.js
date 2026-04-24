// ========== Form Validation ==========

document.addEventListener('DOMContentLoaded', function () {

    // Checkout form validation
    const checkoutForm = document.getElementById('checkoutForm');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', function (e) {
            const name = document.getElementById('name').value.trim();
            const email = document.getElementById('email').value.trim();
            const address = document.getElementById('address').value.trim();

            if (!name || !email || !address) {
                e.preventDefault();
                alert('Please fill in all fields.');
                return false;
            }
        });
    }

    // Payment form validation
    const paymentForm = document.getElementById('paymentForm');
    if (paymentForm) {
        const cardInput = document.getElementById('card_number');
        const expiryInput = document.getElementById('expiry');
        const cvvInput = document.getElementById('cvv');

        // Format card number with spaces
        if (cardInput) {
            cardInput.addEventListener('input', function () {
                let value = this.value.replace(/\D/g, '');
                value = value.replace(/(\d{4})(?=\d)/g, '$1 ');
                this.value = value.substring(0, 19);
            });
        }

        // Format expiry as MM/YY
        if (expiryInput) {
            expiryInput.addEventListener('input', function () {
                let value = this.value.replace(/\D/g, '');
                if (value.length >= 2) {
                    value = value.substring(0, 2) + '/' + value.substring(2);
                }
                this.value = value.substring(0, 5);
            });
        }

        // Allow only digits for CVV
        if (cvvInput) {
            cvvInput.addEventListener('input', function () {
                this.value = this.value.replace(/\D/g, '').substring(0, 4);
            });
        }

        // Validate payment form on submit
        paymentForm.addEventListener('submit', function (e) {
            const cardNumber = cardInput.value.replace(/\s/g, '');
            const expiry = expiryInput.value.trim();
            const cvv = cvvInput.value.trim();

            if (!cardNumber || !expiry || !cvv) {
                e.preventDefault();
                alert('Please fill in all payment fields.');
                return false;
            }

            if (cardNumber.length < 13 || cardNumber.length > 19) {
                e.preventDefault();
                alert('Please enter a valid card number (13-19 digits).');
                return false;
            }

            if (!/^\d{2}\/\d{2}$/.test(expiry)) {
                e.preventDefault();
                alert('Please enter a valid expiry date (MM/YY).');
                return false;
            }

            if (cvv.length < 3 || cvv.length > 4) {
                e.preventDefault();
                alert('Please enter a valid CVV (3-4 digits).');
                return false;
            }
        });
    }
});
