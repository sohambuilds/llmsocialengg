/* FreelanceHub — inbox / conversation UI */

'use strict';

var currentConvId = null;

/* ── Colour map for avatars ── */
var COLORS = {
  conv_001: '#1a73e8',
  conv_002: '#f57c00',
  conv_003: '#7b1fa2',
  conv_004: '#00796b',
  conv_005: '#d32f2f',
};

/* ── Load a conversation into the right panel ── */
function loadConversation(convId) {
  currentConvId = convId;

  /* Mark sidebar item active */
  document.querySelectorAll('.conv-item').forEach(function(el) {
    el.classList.toggle('active', el.dataset.convId === convId);
    if (el.dataset.convId === convId) {
      el.classList.remove('unread');
      var dot = el.querySelector('.unread-dot');
      if (dot) dot.remove();
    }
  });

  fetch('/conversation/' + convId)
    .then(function(r) { return r.json(); })
    .then(function(data) {
      renderConversation(data);
    })
    .catch(function(err) {
      console.error('Failed to load conversation', err);
    });
}

/* ── Render conversation header + messages ── */
function renderConversation(data) {
  var color = COLORS[data.id] || '#555';

  /* Header */
  var avatarEl = document.getElementById('chatAvatar');
  avatarEl.textContent  = data.initials;
  avatarEl.style.background = color;
  avatarEl.style.color = '#fff';
  avatarEl.style.fontWeight = '700';
  avatarEl.style.fontSize = '15px';
  avatarEl.style.borderRadius = '50%';
  avatarEl.style.width = '38px';
  avatarEl.style.height = '38px';
  avatarEl.style.display = 'flex';
  avatarEl.style.alignItems = 'center';
  avatarEl.style.justifyContent = 'center';
  avatarEl.style.flexShrink = '0';

  document.getElementById('chatName').textContent    = data.sender;
  document.getElementById('chatSubject').textContent = data.subject;

  /* Show panels */
  document.getElementById('emptyState').style.display    = 'none';
  document.getElementById('chatHeader').style.display    = 'flex';
  document.getElementById('messagesArea').style.display  = 'block';
  document.getElementById('replyBox').style.display      = 'flex';

  renderMessages(data.messages, data.sender, color);
}

/* ── Render message bubbles ── */
function renderMessages(messages, senderName, color) {
  var area = document.getElementById('messagesArea');
  area.innerHTML = '';

  messages.forEach(function(msg) {
    var isUser = !msg.is_attacker;
    var wrapper = document.createElement('div');
    wrapper.className = 'msg-row ' + (isUser ? 'msg-row--user' : 'msg-row--other');

    if (!isUser) {
      /* Avatar */
      var av = document.createElement('div');
      av.className = 'msg-avatar';
      av.style.background = color;
      av.style.color = '#fff';
      av.style.fontWeight = '700';
      av.style.fontSize = '13px';
      av.textContent = senderName.split(' ').map(function(w) { return w[0]; }).join('').slice(0,2).toUpperCase();
      wrapper.appendChild(av);
    }

    var bubble = document.createElement('div');
    bubble.className = 'msg-bubble ' + (isUser ? 'msg-bubble--user' : 'msg-bubble--other');

    if (msg.html_content) {
      bubble.innerHTML = msg.html_content;
    } else {
      bubble.textContent = msg.content || '';
    }

    var ts = document.createElement('div');
    ts.className = 'msg-ts';
    ts.textContent = msg.timestamp || '';

    var inner = document.createElement('div');
    inner.className = 'msg-inner';
    inner.appendChild(bubble);
    inner.appendChild(ts);

    wrapper.appendChild(inner);
    area.appendChild(wrapper);
  });

  area.scrollTop = area.scrollHeight;
}

/* ── Send reply ── */
function sendReply() {
  if (!currentConvId) return;
  var input = document.getElementById('replyInput');
  var text = input.value.trim();
  if (!text) return;

  var btn = document.getElementById('sendBtn');
  btn.disabled = true;
  input.disabled = true;

  fetch('/reply/' + currentConvId, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: text }),
  })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      input.value = '';
      /* Re-fetch sender info to pass color */
      fetch('/conversation/' + currentConvId)
        .then(function(r2) { return r2.json(); })
        .then(function(conv) {
          renderMessages(data.messages, conv.sender, COLORS[currentConvId] || '#555');
        });
    })
    .catch(function(err) {
      console.error('Send failed', err);
    })
    .finally(function() {
      btn.disabled = false;
      input.disabled = false;
      input.focus();
    });
}

/* ── Keyboard shortcut: Ctrl+Enter to send ── */
document.addEventListener('DOMContentLoaded', function() {
  var replyInput = document.getElementById('replyInput');
  if (replyInput) {
    replyInput.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        sendReply();
      }
    });
  }

  /* Add dynamic styles for message bubbles if not already in CSS */
  if (!document.getElementById('_msg-style')) {
    var s = document.createElement('style');
    s.id = '_msg-style';
    s.textContent = [
      '.messages-area { flex:1; overflow-y:auto; padding:20px 24px; display:flex; flex-direction:column; gap:16px; }',
      '.msg-row { display:flex; gap:10px; max-width:78%; }',
      '.msg-row--user { align-self:flex-end; flex-direction:row-reverse; }',
      '.msg-row--other { align-self:flex-start; }',
      '.msg-avatar { width:32px; height:32px; border-radius:50%; display:flex; align-items:center; justify-content:center; flex-shrink:0; margin-top:2px; }',
      '.msg-inner { display:flex; flex-direction:column; gap:4px; }',
      '.msg-row--user .msg-inner { align-items:flex-end; }',
      '.msg-bubble { padding:10px 14px; border-radius:14px; font-size:13.5px; line-height:1.55; }',
      '.msg-bubble--other { background:#fff; border:1px solid #e0e0e0; border-top-left-radius:4px; color:#1c1c1c; }',
      '.msg-bubble--other a { color:#1a73e8; }',
      '.msg-bubble--user { background:#14a800; color:#fff; border-top-right-radius:4px; }',
      '.msg-ts { font-size:11px; color:#9aa0a6; padding:0 4px; }',
      '.conv-item.active { background:#e8f5e9 !important; border-left:3px solid #14a800; }',
      '.reply-box { display:flex !important; flex-direction:column; padding:16px 20px; border-top:1px solid #e0e0e0; gap:10px; background:#fff; }',
      '.reply-textarea { width:100%; resize:none; border:1px solid #e0e0e0; border-radius:8px; padding:10px 14px; font-size:13.5px; line-height:1.5; outline:none; transition:border .15s; }',
      '.reply-textarea:focus { border-color:#14a800; box-shadow:0 0 0 3px rgba(20,168,0,.12); }',
      '.reply-actions { display:flex; justify-content:space-between; align-items:center; }',
      '.reply-hint { font-size:11.5px; color:#9aa0a6; }',
      '.btn-send { display:flex; align-items:center; gap:6px; padding:8px 18px; background:#14a800; color:#fff; border-radius:6px; font-size:13.5px; font-weight:600; transition:background .15s; }',
      '.btn-send:hover { background:#0d8a00; }',
      '.btn-send:disabled { background:#9ccc65; cursor:not-allowed; }',
    ].join('\n');
    document.head.appendChild(s);
  }
});
