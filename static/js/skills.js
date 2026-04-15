(function(){
  document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("skills-container");
    if (!container) return;

    const searchUrl = container.dataset.searchUrl || "/projects/skills/";
    const addUrl = container.dataset.addUrl || `/projects/${container.dataset.projectId}/skills/add/`;
    const removeUrlTemplate = container.dataset.removeUrlTemplate || `/projects/${container.dataset.projectId}/skills/__ID__/remove/`;

    const addBtn = document.getElementById("add-skill-btn");
    const inputWrapper = document.getElementById("skill-input-wrapper");
    const input = document.getElementById("skill-input");
    const suggestions = document.getElementById("skill-suggestions");

    if (!addBtn || !inputWrapper || !input || !suggestions) return;

    addBtn.addEventListener("click", () => {
      addBtn.classList.add("hidden");
      inputWrapper.classList.remove("hidden");
      input.value = "";
      suggestions.innerHTML = "";
      suggestions.classList.add("hidden");
      input.focus();
    });

    let timeoutId = null;
    input.addEventListener("input", () => {
      const query = input.value.trim();
      clearTimeout(timeoutId);
      if (!query) {
        suggestions.classList.add("hidden");
        suggestions.innerHTML = "";
        return;
      }
      timeoutId = setTimeout(async () => {
        const response = await fetch(`${searchUrl}?q=${encodeURIComponent(query)}`);
        if (!response.ok) return;
        const data = await response.json();

        suggestions.innerHTML = "";
        data.forEach((skill) => {
          const li = document.createElement("li");
          li.textContent = skill.name;
          li.dataset.id = skill.id;
          li.className = "suggestion-item";
          suggestions.appendChild(li);
        });

        const exact = data.some((skill) => skill.name.toLowerCase() === query.toLowerCase());
        if (!exact) {
          const liNew = document.createElement("li");
          liNew.textContent = `Создать «${query}»`;
          liNew.dataset.name = query;
          liNew.className = "create-new";
          suggestions.appendChild(liNew);
        }

        suggestions.classList.remove("hidden");
      }, 200);
    });

    suggestions.addEventListener("mousedown", async (e) => {
      const li = e.target.closest("li");
      if (!li) return;

      if (li.classList.contains("create-new")) {
        await addSkillByName(li.dataset.name);
      } else if (li.dataset.id) {
        await addSkillById(li.dataset.id);
      }
      hideInput();
    });

    input.addEventListener("keydown", async (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        const query = input.value.trim();
        if (!query) return;

        const first = suggestions.querySelector("li");
        if (first && first.dataset.id) {
          await addSkillById(first.dataset.id);
        } else {
          await addSkillByName(query);
        }
        hideInput();
      }
      if (e.key === "Escape") {
        hideInput();
      }
    });

    input.addEventListener("blur", () => setTimeout(hideInput, 120));

    function hideInput() {
      inputWrapper.classList.add("hidden");
      suggestions.classList.add("hidden");
      addBtn.classList.remove("hidden");
    }

    container.addEventListener("click", async (e) => {
      if (e.target.classList.contains("remove-skill-btn")) {
        const chip = e.target.closest(".skill-chip");
        const skillId = chip.dataset.id;
        const response = await fetch(removeUrlTemplate.replace("__ID__", skillId), {
          method: "POST",
          headers: { "X-CSRFToken": getCookie("csrftoken") }
        });
        if (response.ok) {
          chip.remove();
          if (!container.querySelector('.skill-chip')) {
            const empty = document.createElement('span');
            empty.className = 'skill-empty';
            empty.textContent = 'Навыки не указаны';
            container.insertBefore(empty, addBtn);
          }
        }
      }
    });

    async function addSkillById(skillId) {
      const response = await fetch(addUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ skill_id: skillId }),
      });
      if (response.ok) {
        const skill = await response.json();
        appendChip(skill.id, skill.name);
      }
    }

    async function addSkillByName(name) {
      const response = await fetch(addUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ name }),
      });
      if (response.ok) {
        const skill = await response.json();
        appendChip(skill.id, skill.name);
      }
    }

    function appendChip(id, name) {
      if (container.querySelector(`.skill-chip[data-id="${id}"]`)) return;

      const chip = document.createElement("span");
      chip.className = "skill-chip";
      chip.dataset.id = id;
      chip.innerHTML = `${name} <button type="button" class="remove-skill-btn" aria-label="Удалить" title="Удалить">×</button>`;

      container.insertBefore(chip, addBtn);
      const empty = container.querySelector(".skill-empty");
      if (empty) empty.remove();
    }

    function getCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
          cookie = cookie.trim();
          if (cookie.startsWith(name + "=")) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    }
  });
})();
