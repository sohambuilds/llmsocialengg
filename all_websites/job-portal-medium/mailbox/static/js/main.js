/**
 * Gmail Clone - Mailbox JavaScript
 * Handles inbox interactions, category filtering, and email navigation.
 */

document.addEventListener('DOMContentLoaded', function () {

    // ==================== CATEGORY TAB FILTERING ====================
    const tabs = document.querySelectorAll('.tab');
    const emailRows = document.querySelectorAll('.email-row');

    tabs.forEach(tab => {
        tab.addEventListener('click', function () {
            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');

            const category = this.dataset.category;

            // Show/hide emails based on category
            emailRows.forEach(row => {
                if (category === 'all' || row.dataset.category === category) {
                    row.style.display = 'flex';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    });

    // ==================== STAR TOGGLE ====================
    document.querySelectorAll('.email-star').forEach(star => {
        // Set initial state from icon text
        const icon = star.querySelector('.material-icons');
        if (icon && icon.textContent.trim() === 'star') {
            star.classList.add('starred');
        }

        star.addEventListener('click', function (e) {
            e.stopPropagation();
            this.classList.toggle('starred');
            const iconEl = this.querySelector('.material-icons');
            if (this.classList.contains('starred')) {
                iconEl.textContent = 'star';
            } else {
                iconEl.textContent = 'star_border';
            }
        });
    });

    // ==================== SELECT ALL ====================
    const selectAll = document.getElementById('selectAll');
    if (selectAll) {
        selectAll.addEventListener('change', function () {
            document.querySelectorAll('.email-checkbox').forEach(cb => {
                cb.checked = this.checked;
            });
        });
    }

    // ==================== SEARCH ====================
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function () {
            const query = this.value.toLowerCase();
            emailRows.forEach(row => {
                const sender = row.querySelector('.email-sender')?.textContent.toLowerCase() || '';
                const subject = row.querySelector('.email-subject')?.textContent.toLowerCase() || '';
                const preview = row.querySelector('.email-preview')?.textContent.toLowerCase() || '';

                if (sender.includes(query) || subject.includes(query) || preview.includes(query)) {
                    row.style.display = 'flex';
                } else {
                    row.style.display = 'none';
                }
            });

            // If search is cleared, re-apply category filter
            if (!query) {
                const activeTab = document.querySelector('.tab.active');
                if (activeTab) {
                    activeTab.click();
                }
            }
        });
    }

    // ==================== KEYBOARD SHORTCUTS ====================
    document.addEventListener('keydown', function (e) {
        // Don't trigger shortcuts when typing in inputs
        if (e.target.tagName === 'INPUT' || e.target.isContentEditable) return;

        switch (e.key) {
            case 'c':
                // Compose (no-op for benchmark)
                break;
            case '/':
                e.preventDefault();
                if (searchInput) searchInput.focus();
                break;
        }
    });
});
