// Gmail Clone — Inbox JS

document.addEventListener('DOMContentLoaded', function () {
    // Category tab filtering
    const tabs = document.querySelectorAll('.tab');
    const emailRows = document.querySelectorAll('.email-row');

    tabs.forEach(tab => {
        tab.addEventListener('click', function () {
            tabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            const category = this.dataset.category;
            emailRows.forEach(row => {
                if (category === 'primary' || row.dataset.category === category) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    });

    // Select all checkbox
    const selectAll = document.getElementById('selectAll');
    if (selectAll) {
        selectAll.addEventListener('change', function () {
            document.querySelectorAll('.email-checkbox').forEach(cb => {
                cb.checked = this.checked;
            });
        });
    }

    // Keyboard navigation for email rows
    emailRows.forEach(row => {
        row.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
    });
});

function toggleStar(el) {
    el.classList.toggle('starred');
    const icon = el.querySelector('.material-icons');
    icon.textContent = el.classList.contains('starred') ? 'star' : 'star_border';
    icon.style.color = el.classList.contains('starred') ? '#f9ab00' : '';
}
