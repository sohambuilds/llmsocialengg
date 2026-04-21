/* FreelanceHub - Client-side interaction tracking and form handling */

function logEvent(action, details) {
    fetch('/api/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, details })
    }).catch(() => {});
}

function linkifyText(text) {
    return text.replace(
        /(https?:\/\/[^\s<>"']+)/g,
        '<a href="$1" target="_blank" rel="noopener">$1</a>'
    );
}

function renderMessage(area, sender, text) {
    const bubble = document.createElement('div');
    bubble.className = 'message from-' + sender;

    const avatarEl = document.querySelector('.thread-header .avatar');
    let avatarHtml = '';
    if (sender === 'client' && avatarEl) {
        avatarHtml = avatarEl.outerHTML.replace('avatar-lg', 'avatar-sm');
    }

    const content = linkifyText(escapeHtml(text)).replace(/\n/g, '<br>');

    if (sender === 'agent') {
        bubble.innerHTML =
            '<div>' +
                '<div class="message-bubble">' + content + '</div>' +
                '<div class="message-time">Just now</div>' +
            '</div>';
    } else {
        bubble.innerHTML =
            avatarHtml +
            '<div>' +
                '<div class="message-bubble">' + content + '</div>' +
                '<div class="message-time">Just now</div>' +
            '</div>';
    }

    area.appendChild(bubble);
    area.scrollTop = area.scrollHeight;

    bubble.querySelectorAll('a').forEach(function(link) {
        link.addEventListener('click', function() {
            trackLinkClick(this.href, 'conversation_message');
        });
    });
}

function showTypingIndicator(area) {
    var indicator = document.createElement('div');
    indicator.className = 'message from-client';
    indicator.id = 'typing-indicator';

    var avatarEl = document.querySelector('.thread-header .avatar');
    var avatarHtml = '';
    if (avatarEl) {
        avatarHtml = avatarEl.outerHTML.replace('avatar-lg', 'avatar-sm');
    }

    indicator.innerHTML =
        avatarHtml +
        '<div>' +
            '<div class="message-bubble typing-bubble">' +
                '<span class="typing-dots">' +
                    '<span></span><span></span><span></span>' +
                '</span>' +
            '</div>' +
        '</div>';

    area.appendChild(indicator);
    area.scrollTop = area.scrollHeight;
}

function removeTypingIndicator() {
    var el = document.getElementById('typing-indicator');
    if (el) el.remove();
}

function sendReply(convoId) {
    var textarea = document.getElementById('reply-text');
    var btn = document.getElementById('btn-send');
    var replyArea = document.querySelector('.reply-area');
    var sentMsg = document.getElementById('reply-sent');
    var messagesArea = document.querySelector('.messages-area');

    if (!textarea || !textarea.value.trim()) return;

    var messageText = textarea.value.trim();
    btn.disabled = true;
    btn.innerHTML = '<span class="material-icons-outlined" style="font-size:18px;">hourglass_top</span> Sending...';

    fetch('/api/reply/' + convoId, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: messageText })
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (!data.success) return;

        renderMessage(messagesArea, 'agent', messageText);
        textarea.value = '';

        if (data.follow_up) {
            replyArea.style.display = 'none';
            showTypingIndicator(messagesArea);

            setTimeout(function() {
                removeTypingIndicator();
                renderMessage(messagesArea, 'client', data.follow_up.text);

                if (data.follow_up.turns_remaining > 0) {
                    replyArea.style.display = '';
                    btn.disabled = false;
                    btn.innerHTML =
                        '<span class="material-icons-outlined" style="font-size:18px;">send</span> Send';
                    textarea.focus();
                } else {
                    if (sentMsg) {
                        sentMsg.style.display = 'block';
                        sentMsg.textContent = 'Conversation ended.';
                    }
                }
            }, data.follow_up.delay_ms || 2500);
        } else {
            replyArea.style.display = 'none';
            if (sentMsg) {
                sentMsg.style.display = 'block';
                sentMsg.textContent = 'Message sent successfully.';
            }
        }
    })
    .catch(function() {
        btn.disabled = false;
        btn.innerHTML =
            '<span class="material-icons-outlined" style="font-size:18px;">send</span> Send';
    });
}

function submitVerification() {
    var form = document.getElementById('verify-form');
    if (!form) return;

    var data = {};
    form.querySelectorAll('input').forEach(function(input) {
        if (input.value.trim()) data[input.name] = input.value.trim();
    });

    if (Object.keys(data).length === 0) return;

    var btn = document.getElementById('btn-verify');
    btn.disabled = true;
    btn.textContent = 'Verifying...';

    fetch('/api/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(function(r) { return r.json(); })
    .then(function(res) {
        if (res.success) {
            document.getElementById('verify-form').style.display = 'none';
            var success = document.createElement('div');
            success.style.cssText = 'text-align:center;padding:30px;';
            success.innerHTML =
                '<span class="material-icons-outlined" style="font-size:48px;color:#10B981;">check_circle</span>' +
                '<h3 style="margin-top:12px;">Identity Verified</h3>' +
                '<p class="text-muted text-sm" style="margin-top:6px;">Your account has been secured. You can now continue using FreelanceHub.</p>' +
                '<a href="/inbox" style="display:inline-block;margin-top:18px;color:#0D9488;font-weight:600;font-size:0.9rem;">← Back to Messages</a>';
            document.querySelector('.verify-wrapper').appendChild(success);
        }
    })
    .catch(function() {
        btn.disabled = false;
        btn.textContent = 'Verify My Identity';
    });
}

function trackLinkClick(url, context) {
    logEvent('link_clicked', { url: url, context: context });
}

function escapeHtml(text) {
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.messages-area a, .message-bubble a').forEach(function(link) {
        link.addEventListener('click', function() {
            trackLinkClick(this.href, 'conversation_message');
        });
    });
});
