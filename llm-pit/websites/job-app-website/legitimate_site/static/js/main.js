// Google Careers Legitimate Site — JS

document.addEventListener('DOMContentLoaded', function () {
    // Filter chips (cosmetic only)
    document.querySelectorAll('.filter-chip').forEach(chip => {
        chip.addEventListener('click', function () {
            document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
            this.classList.add('active');
        });
    });
});
