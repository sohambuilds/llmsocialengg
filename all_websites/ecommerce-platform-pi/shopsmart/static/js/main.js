// ShopSmart — Main JavaScript

document.addEventListener('DOMContentLoaded', function () {

    // ── Buy button click tracking ──
    document.querySelectorAll('.buy-button').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var store = btn.getAttribute('data-store');
            var listing = btn.getAttribute('data-listing');
            if (store || listing) {
                fetch('/api/log', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        action: 'buy_button_click',
                        details: { store: store, listing: listing }
                    })
                });
            }
        });
    });

    // ── Notification action click tracking ──
    document.querySelectorAll('.notif-action-btn').forEach(function (link) {
        link.addEventListener('click', function () {
            fetch('/api/log', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action: 'notification_click',
                    details: { href: link.getAttribute('href') }
                })
            });
        });
    });

    // ── Search bar interaction ──
    var searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('focus', function () {
            this.parentElement.classList.add('search-focused');
        });
        searchInput.addEventListener('blur', function () {
            this.parentElement.classList.remove('search-focused');
        });
        searchInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                // no-op: search is decorative
            }
        });
    }

    // ── Notification badge update ──
    var badge = document.getElementById('notifBadge');
    if (badge) {
        fetch('/notifications')
            .then(function (r) { return r.text(); })
            .then(function (html) {
                var parser = new DOMParser();
                var doc = parser.parseFromString(html, 'text/html');
                var count = doc.querySelectorAll('.notification-card').length;
                if (count > 0) {
                    badge.textContent = count;
                    badge.style.display = 'flex';
                } else {
                    badge.style.display = 'none';
                }
            })
            .catch(function () {
                // fail silently
            });
    }

    // ── Smooth scroll-in animation for listing rows ──
    var rows = document.querySelectorAll('.listing-row, .notification-card, .review-card');
    if ('IntersectionObserver' in window && rows.length > 0) {
        rows.forEach(function (el) {
            el.style.opacity = '0';
            el.style.transform = 'translateY(12px)';
            el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        });

        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

        rows.forEach(function (el) { observer.observe(el); });
    }
});

// ── Toggle reviews (global, called from inline onclick) ──
function toggleReviews(listingId) {
    var body = document.getElementById('reviews-body-' + listingId);
    var arrow = body.parentElement.querySelector('.toggle-arrow');
    if (body && arrow) {
        body.classList.toggle('expanded');
        arrow.classList.toggle('rotated');
    }
}
