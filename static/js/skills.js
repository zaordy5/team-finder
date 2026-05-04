(function () {
  const SEARCH_DELAY_MS = 200;
  const BLUR_CLOSE_DELAY_MS = 120;

  document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("skills-container");

    if (!container) {
      return;
    }

    const searchUrl = container.dataset.searchUrl;
    const addUrl = container.dataset.addUrl;
    const removeUrlTemplate = container.dataset.removeUrlTemplate;

    const addButton = document.getElementById("add-skill-btn");
    const inputWrapper = document.getElementById("skill-input-wrapper");
    const input = document.getElementById("skill-input");
    const suggestions = document.getElementById("skill-suggestions");

    if (!searchUrl || !addUrl || !removeUrlTemplate || !addButton || !inputWrapper || !input || !suggestions) {
      return;
    }

    let timeoutId = null;

    function hideInput() {
      inputWrapper.classList.add("hidden");
      suggestions.classList.add("hidden");
      addButton.classList.remove("hidden");
    }

    function clearSuggestions() {
      suggestions.innerHTML = "";
      suggestions.classList.add("hidden");
    }

    function showToast(message, type = "info") {
      if (window.toast) {
        window.toast(message, { type });
      }
    }

    async function addSkillByPayload(payload) {
      const response = await fetch(addUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": window.getCookie ? window.getCookie("csrftoken") : "",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok || data.status === "error") {
        showToast(data.message || "Не удалось добавить навык", "error");
        return;
      }

      appendChip(data.id, data.name);
      showToast(data.message || "Навык добавлен");
    }

    function appendChip(id, name) {
      if (container.querySelector(`.skill-chip[data-id="${id}"]`)) {
        return;
      }

      const chip = document.createElement("span");
      chip.className = "skill-chip";
      chip.dataset.id = id;
      chip.innerHTML = `${name} <button type="button" class="remove-skill-btn" aria-label="Удалить" title="Удалить">×</button>`;

      container.insertBefore(chip, addButton);

      const empty = container.querySelector(".skill-empty");
      if (empty) {
        empty.remove();
      }
    }

    async function loadSuggestions(query) {
      try {
        const response = await fetch(`${searchUrl}?q=${encodeURIComponent(query)}`);

        if (!response.ok) {
          return;
        }

        const data = await response.json();
        suggestions.innerHTML = "";

        data.forEach((skill) => {
          const item = document.createElement("li");
          item.textContent = skill.name;
          item.dataset.id = skill.id;
          item.className = "suggestion-item";
          suggestions.appendChild(item);
        });

        const hasExactMatch = data.some(
          (skill) => skill.name.toLowerCase() === query.toLowerCase(),
        );

        // Если точного совпадения нет, пользователь может создать новый навык.
        if (!hasExactMatch) {
          const newItem = document.createElement("li");
          newItem.textContent = `Создать «${query}»`;
          newItem.dataset.name = query;
          newItem.className = "create-new";
          suggestions.appendChild(newItem);
        }

        suggestions.classList.remove("hidden");
      } catch (error) {
        console.error("Ошибка поиска навыков:", error);
      }
    }

    addButton.addEventListener("click", () => {
      addButton.classList.add("hidden");
      inputWrapper.classList.remove("hidden");
      input.value = "";
      clearSuggestions();
      input.focus();
    });

    input.addEventListener("input", () => {
      const query = input.value.trim();
      clearTimeout(timeoutId);

      if (!query) {
        clearSuggestions();
        return;
      }

      timeoutId = setTimeout(() => loadSuggestions(query), SEARCH_DELAY_MS);
    });

    suggestions.addEventListener("mousedown", async (event) => {
      const item = event.target.closest("li");

      if (!item) {
        return;
      }

      if (item.classList.contains("create-new")) {
        await addSkillByPayload({ name: item.dataset.name });
      } else if (item.dataset.id) {
        await addSkillByPayload({ skill_id: item.dataset.id });
      }

      hideInput();
    });

    input.addEventListener("keydown", async (event) => {
      if (event.key === "Escape") {
        hideInput();
        return;
      }

      if (event.key !== "Enter") {
        return;
      }

      event.preventDefault();

      const query = input.value.trim();
      if (!query) {
        return;
      }

      const firstSuggestion = suggestions.querySelector("li");

      if (firstSuggestion && firstSuggestion.dataset.id) {
        await addSkillByPayload({ skill_id: firstSuggestion.dataset.id });
      } else {
        await addSkillByPayload({ name: query });
      }

      hideInput();
    });

    input.addEventListener("blur", () => {
      setTimeout(hideInput, BLUR_CLOSE_DELAY_MS);
    });

    container.addEventListener("click", async (event) => {
      if (!event.target.classList.contains("remove-skill-btn")) {
        return;
      }

      const chip = event.target.closest(".skill-chip");
      if (!chip) {
        return;
      }

      const response = await fetch(removeUrlTemplate.replace("__ID__", chip.dataset.id), {
        method: "POST",
        headers: {
          "X-CSRFToken": window.getCookie ? window.getCookie("csrftoken") : "",
        },
      });

      const data = await response.json();

      if (!response.ok || data.status !== "ok") {
        showToast(data.message || "Не удалось удалить навык", "error");
        return;
      }

      chip.remove();

      if (!container.querySelector(".skill-chip")) {
        const empty = document.createElement("span");
        empty.className = "skill-empty";
        empty.textContent = "Навыки не указаны";
        container.insertBefore(empty, addButton);
      }

      showToast(data.message || "Навык удалён");
    });
  });
})();
