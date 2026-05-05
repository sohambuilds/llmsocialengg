// Prevent empty form submissions with basic validation
document.addEventListener("DOMContentLoaded", function () {
    const forms = document.querySelectorAll("form");

    forms.forEach(function (form) {
        form.addEventListener("submit", function (e) {
            const inputs = form.querySelectorAll("input[required]");
            let valid = true;

            inputs.forEach(function (input) {
                if (!input.value.trim()) {
                    valid = false;
                    input.style.borderColor = "#ef4444";
                    input.addEventListener(
                        "input",
                        function () {
                            input.style.borderColor = "";
                        },
                        { once: true }
                    );
                }
            });

            if (!valid) {
                e.preventDefault();
            }
        });
    });

    // Button press feedback
    document.querySelectorAll(".btn, .btn-gh-signin").forEach(function (btn) {
        btn.addEventListener("mousedown", function () {
            btn.style.opacity = "0.85";
        });
        btn.addEventListener("mouseup", function () {
            btn.style.opacity = "";
        });
        btn.addEventListener("mouseleave", function () {
            btn.style.opacity = "";
        });
    });
});
