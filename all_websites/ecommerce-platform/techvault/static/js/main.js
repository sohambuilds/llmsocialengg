// TechVault — Main JavaScript
document.addEventListener('DOMContentLoaded', function() {

    // ---- Color swatch selection ----
    document.querySelectorAll('.color-swatch').forEach(function(swatch) {
        swatch.addEventListener('click', function() {
            document.querySelectorAll('.color-swatch').forEach(function(s) {
                s.classList.remove('active');
            });
            swatch.classList.add('active');
            var colorLabel = document.getElementById('selectedColor');
            if (colorLabel) {
                colorLabel.textContent = swatch.getAttribute('data-color');
            }
        });
    });

    // ---- Quantity selector ----
    var qtyInput = document.getElementById('qtyInput');
    var qtyMinus = document.getElementById('qtyMinus');
    var qtyPlus = document.getElementById('qtyPlus');

    if (qtyInput && qtyMinus && qtyPlus) {
        qtyMinus.addEventListener('click', function() {
            var val = parseInt(qtyInput.value, 10) || 1;
            if (val > 1) qtyInput.value = val - 1;
        });
        qtyPlus.addEventListener('click', function() {
            var val = parseInt(qtyInput.value, 10) || 1;
            if (val < 10) qtyInput.value = val + 1;
        });
        qtyInput.addEventListener('change', function() {
            var val = parseInt(this.value, 10);
            if (isNaN(val) || val < 1) this.value = 1;
            if (val > 10) this.value = 10;
        });
    }

    // ---- Tab switching ----
    document.querySelectorAll('.tab-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var tabId = btn.getAttribute('data-tab');
            // Deactivate all tabs
            document.querySelectorAll('.tab-btn').forEach(function(b) { b.classList.remove('active'); });
            document.querySelectorAll('.tab-content').forEach(function(c) { c.classList.remove('active'); });
            // Activate selected
            btn.classList.add('active');
            var panel = document.getElementById('tab-' + tabId);
            if (panel) panel.classList.add('active');
        });
    });

    // ---- Gallery thumbnail selection ----
    document.querySelectorAll('.gallery-thumbs .thumb').forEach(function(thumb) {
        thumb.addEventListener('click', function() {
            document.querySelectorAll('.gallery-thumbs .thumb').forEach(function(t) {
                t.classList.remove('active');
            });
            thumb.classList.add('active');
        });
    });

    // ---- Search bar interaction ----
    var searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                // No actual search — just visual interaction
            }
        });
    }

    // ---- Smooth scroll for anchor links ----
    document.querySelectorAll('a[href^="#"]').forEach(function(link) {
        link.addEventListener('click', function(e) {
            var target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
});
