(function () {
  if (!window.getCookie) {
    window.getCookie = function (name) {
      let cookieValue = null;

      if (!document.cookie || document.cookie === "") {
        return cookieValue;
      }

      const cookies = document.cookie.split(";");

      for (let cookie of cookies) {
        cookie = cookie.trim();

        if (cookie.startsWith(`${name}=`)) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }

      return cookieValue;
    };
  }

  if (!window.toast) {
    function ensureToastContainer() {
      let container = document.getElementById("tf-toast-container");

      if (container) {
        return container;
      }

      container = document.createElement("div");
      container.id = "tf-toast-container";
      container.style.position = "fixed";
      container.style.left = "50%";
      container.style.top = "50%";
      container.style.transform = "translate(-50%, -50%)";
      container.style.display = "flex";
      container.style.flexDirection = "column";
      container.style.alignItems = "center";
      container.style.gap = "8px";
      container.style.zIndex = "2147483647";
      document.body.appendChild(container);

      return container;
    }

    window.toast = function (message, options = {}) {
      const { type = "info", duration = 2200 } = options;
      const container = ensureToastContainer();

      const element = document.createElement("div");
      element.textContent = message;
      element.style.maxWidth = "90vw";
      element.style.background = (
        type === "error" ? "rgba(220, 38, 38, 0.95)" : "rgba(17, 17, 17, 0.92)"
      );
      element.style.color = "#fff";
      element.style.padding = "12px 16px";
      element.style.borderRadius = "8px";
      element.style.boxShadow = "0 6px 20px rgba(0, 0, 0, 0.25)";
      element.style.fontSize = "14px";
      element.style.lineHeight = "1.35";
      element.style.wordBreak = "break-word";
      element.style.textAlign = "center";
      element.style.opacity = "0";
      element.style.transition = "opacity 180ms ease";

      container.appendChild(element);
      requestAnimationFrame(() => {
        element.style.opacity = "1";
      });

      setTimeout(() => {
        element.style.opacity = "0";
        setTimeout(() => element.remove(), 200);
      }, Math.max(1200, duration));
    };
  }
})();
