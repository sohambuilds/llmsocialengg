// ===== Form Validation =====

document.addEventListener("DOMContentLoaded", function () {

    // --- Summarize Form Validation ---
    const summarizeForm = document.getElementById("summarize-form");
    if (summarizeForm) {
        const textInput = document.getElementById("text-input");

        summarizeForm.addEventListener("submit", function (e) {
            removeError(textInput);

            if (!textInput.value.trim()) {
                e.preventDefault();
                showError(textInput, "Please paste some text to summarize.");
                textInput.focus();
            }
        });
    }

    // --- Premium Form Validation ---
    const premiumForm = document.getElementById("premium-form");
    if (premiumForm) {
        const apiKeyInput = document.getElementById("api_key");

        premiumForm.addEventListener("submit", function (e) {
            removeError(apiKeyInput);

            if (!apiKeyInput.value.trim()) {
                e.preventDefault();
                showError(apiKeyInput, "Please enter your API key.");
                apiKeyInput.focus();
            }
        });
    }

});


// ===== Helper Functions =====

function showError(inputEl, message) {
    let errorEl = inputEl.parentElement.querySelector(".error-msg");

    if (!errorEl) {
        errorEl = document.createElement("p");
        errorEl.className = "error-msg";
        inputEl.parentElement.appendChild(errorEl);
    }

    errorEl.textContent = message;
    errorEl.classList.add("show");
    inputEl.style.borderColor = "#e74c3c";
}

function removeError(inputEl) {
    const errorEl = inputEl.parentElement.querySelector(".error-msg");
    if (errorEl) {
        errorEl.classList.remove("show");
    }
    inputEl.style.borderColor = "";
}
