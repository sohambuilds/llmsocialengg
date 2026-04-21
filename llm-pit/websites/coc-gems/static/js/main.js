// Searchly — search form handler
document.addEventListener('DOMContentLoaded', function () {
  const forms = document.querySelectorAll('.searchly-form');
  forms.forEach(function (form) {
    form.addEventListener('submit', function (e) {
      const input = form.querySelector('input[name="q"]');
      if (!input || !input.value.trim()) {
        e.preventDefault();
        input && input.focus();
      }
    });
  });
});
