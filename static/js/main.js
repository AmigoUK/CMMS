/* CMMS — Main JavaScript */

// Auto-show Bootstrap toasts on page load
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".toast").forEach(function (el) {
        new bootstrap.Toast(el).show();
    });
});

// CSRF token helper for fetch requests
function getCsrfToken() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") : "";
}

// POST helper with CSRF
function postAction(url, data) {
    var form = document.createElement("form");
    form.method = "POST";
    form.action = url;

    var csrf = document.createElement("input");
    csrf.type = "hidden";
    csrf.name = "csrf_token";
    csrf.value = getCsrfToken();
    form.appendChild(csrf);

    if (data) {
        Object.keys(data).forEach(function (key) {
            var input = document.createElement("input");
            input.type = "hidden";
            input.name = key;
            input.value = data[key];
            form.appendChild(input);
        });
    }

    document.body.appendChild(form);
    form.submit();
}

// Confirm delete modal handler
document.addEventListener("DOMContentLoaded", function () {
    var confirmModal = document.getElementById("confirmModal");
    if (confirmModal) {
        confirmModal.addEventListener("show.bs.modal", function (event) {
            var btn = event.relatedTarget;
            var action = btn.getAttribute("data-action");
            var message = btn.getAttribute("data-message") || "Are you sure?";
            confirmModal.querySelector(".modal-body p").textContent = message;
            confirmModal.querySelector("#confirmForm").action = action;
        });
    }
});
