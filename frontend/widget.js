(function (window, document) {
  "use strict";

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function createEl(tag, className, html) {
    var el = document.createElement(tag);
    if (className) el.className = className;
    if (html !== undefined) el.innerHTML = html;
    return el;
  }

  function mount(selector, options) {
    var root = typeof selector === "string" ? document.querySelector(selector) : selector;
    if (!root) return;

    var settings = options || {};
    var apiBase = (settings.apiBase || window.location.origin || "").replace(/\/$/, "");

    root.innerHTML = "";
    var widget = createEl("section", "dostbin-widget");
    widget.innerHTML =
      '<div class="dostbin-header"><h2>DOSTBin Assistant</h2><p>Ask about products, pricing, and composting.</p></div>' +
      '<div class="dostbin-messages" role="log" aria-live="polite"></div>' +
      '<form class="dostbin-form">' +
      '<input type="text" name="message" maxlength="500" autocomplete="off" placeholder="Ask a question..." aria-label="Your question" required />' +
      '<button type="submit">Send</button>' +
      "</form>";

    var messages = widget.querySelector(".dostbin-messages");
    var form = widget.querySelector("form");
    var input = widget.querySelector("input");
    var button = widget.querySelector("button");

    function addBubble(text, className) {
      messages.appendChild(createEl("div", "dostbin-bubble " + className, escapeHtml(text)));
      messages.scrollTop = messages.scrollHeight;
    }

    addBubble("Hi! I can help with DOSTBin models, pricing, usage, and support.", "bot");

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var message = (input.value || "").trim();
      if (!message) {
        addBubble("Please enter a question.", "error");
        return;
      }
      if (message.length > 500) {
        addBubble("Please keep questions under 500 characters.", "error");
        return;
      }

      addBubble(message, "user");
      input.value = "";
      button.disabled = true;
      addBubble("Thinking...", "muted");
      var loading = messages.lastChild;

      fetch(apiBase + "/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message }),
      })
        .then(function (res) {
          return res.json().then(function (data) {
            return { ok: res.ok, status: res.status, data: data };
          });
        })
        .then(function (result) {
          if (loading && loading.parentNode) loading.parentNode.removeChild(loading);
          if (result.data && result.data.success && result.data.response) {
            addBubble(result.data.response, "bot");
            return;
          }
          var errorText =
            (result.data && (result.data.error || result.data.detail)) ||
            "Something went wrong. Please try again.";
          addBubble(typeof errorText === "string" ? errorText : "Request failed.", "error");
        })
        .catch(function () {
          if (loading && loading.parentNode) loading.parentNode.removeChild(loading);
          addBubble("Could not reach the DOSTBin assistant. Check the API URL and try again.", "error");
        })
        .then(function () {
          button.disabled = false;
          input.focus();
        });
    });

    root.appendChild(widget);
  }

  window.DostbinChat = { mount: mount };
})(window, document);
