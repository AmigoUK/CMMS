/* Shared bulk-action bar behaviour.
 *
 * Self-activates on any <form data-bulk-form>. Reveals the bulk-action bar
 * when at least one row checkbox (.bulk-cb) is ticked, wires up the master
 * "select page" checkbox, the "select all matching" / "clear" controls, the
 * action-specific sub-input panels, and a confirm step for destructive
 * actions. Vanilla JS — no build step, matches the app's existing style.
 */
(function () {
  "use strict";

  function initForm(form) {
    var bar = form.querySelector("[data-bulk-bar]");
    if (!bar) { return; }

    var master = form.querySelector("[data-bulk-master]");
    var countEl = bar.querySelector("[data-bulk-count]");
    var scopeEl = bar.querySelector("[data-bulk-scope]");
    var actionSelect = bar.querySelector("[data-bulk-action-select]");
    var applyBtn = bar.querySelector("[data-bulk-apply]");
    var clearBtn = bar.querySelector("[data-bulk-clear]");
    var matchingBtn = bar.querySelector("[data-bulk-select-all-matching]");
    var subInputs = form.querySelectorAll("[data-bulk-for]");
    var filteredMode = false;

    function boxes() {
      return Array.prototype.slice.call(form.querySelectorAll(".bulk-cb"));
    }
    function checkedBoxes() {
      return boxes().filter(function (cb) { return cb.checked; });
    }

    function refresh() {
      var all = boxes();
      var n = checkedBoxes().length;

      if (filteredMode && matchingBtn) {
        countEl.textContent = matchingBtn.getAttribute("data-total");
      } else {
        countEl.textContent = String(n);
      }

      bar.hidden = n === 0;

      if (master) {
        master.checked = n > 0 && n === all.length;
        master.indeterminate = n > 0 && n < all.length;
      }
      applyBtn.disabled = n === 0 || !actionSelect.value;
    }

    function clearFiltered() {
      if (filteredMode) {
        filteredMode = false;
        if (scopeEl) { scopeEl.value = "page"; }
      }
    }

    boxes().forEach(function (cb) {
      cb.addEventListener("change", function () {
        if (!cb.checked) { clearFiltered(); }
        refresh();
      });
    });

    if (master) {
      master.addEventListener("change", function () {
        boxes().forEach(function (cb) { cb.checked = master.checked; });
        clearFiltered();
        refresh();
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener("click", function () {
        boxes().forEach(function (cb) { cb.checked = false; });
        clearFiltered();
        refresh();
      });
    }

    if (matchingBtn) {
      matchingBtn.addEventListener("click", function () {
        boxes().forEach(function (cb) { cb.checked = true; });
        filteredMode = true;
        if (scopeEl) { scopeEl.value = "filtered"; }
        refresh();
      });
    }

    function showSubInputs(action) {
      Array.prototype.forEach.call(subInputs, function (wrap) {
        var match = wrap.getAttribute("data-bulk-for") === action;
        wrap.hidden = !match;
        // Disable controls in hidden panels so stale values never submit.
        wrap.querySelectorAll("input, select, textarea").forEach(function (el) {
          el.disabled = !match;
        });
      });
    }
    showSubInputs(null);

    actionSelect.addEventListener("change", function () {
      showSubInputs(actionSelect.value);
      refresh();
    });

    form.addEventListener("submit", function (e) {
      if (checkedBoxes().length === 0) {
        e.preventDefault();
        return;
      }
      var opt = actionSelect.options[actionSelect.selectedIndex];
      if (opt && opt.getAttribute("data-confirm") === "1") {
        var msg = form.getAttribute("data-bulk-confirm-text") ||
                  "Apply this action to the selected rows?";
        if (!window.confirm(msg)) {
          e.preventDefault();
        }
      }
    });

    refresh();
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-bulk-form]").forEach(initForm);
  });
})();
