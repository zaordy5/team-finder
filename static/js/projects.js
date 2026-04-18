(function(){
  document.addEventListener("DOMContentLoaded", function() {
    const completeBtn = document.getElementById("complete-project-btn");
    if (completeBtn) {
      completeBtn.addEventListener("click", async function(e) {
        e.preventDefault();
        const actionUrl = completeBtn.dataset.actionUrl;
        if (!actionUrl) return;

        try {
          const response = await fetch(actionUrl, {
            method: "POST",
            headers: {
              "X-CSRFToken": window.getCookie ? window.getCookie("csrftoken") : "",
              "Content-Type": "application/json"
            },
            body: JSON.stringify({})
          });
          const data = await response.json();

          if (!response.ok || data.status !== "ok") {
            const message = data.message || "Ошибка при завершении проекта";
            if (window.toast) window.toast(message, { type: 'error' });
            else alert(message);
            return;
          }

          const statusEl = document.querySelector(".project-status-black");
          if (statusEl && data.project_status === "closed") {
            statusEl.textContent = "Закрыт";
          }
          completeBtn.remove();
          if (window.toast) window.toast(data.message || "Проект завершён", { type: 'info' });
        } catch (err) {
          console.error("Ошибка запроса:", err);
          if (window.toast) window.toast("Ошибка сети", { type: 'error' });
        }
      });
    }

    const participateBtn = document.getElementById("participate-btn");
    const participantsList = document.getElementById("participants-list");
    const participantsCount = document.getElementById("participants-count");
    if (participateBtn && participantsList && participantsCount) {
      const userId = participateBtn.dataset.userId || null;
      const actionUrl = participateBtn.dataset.actionUrl;
      const userName = participateBtn.dataset.userName || "";
      const userAvatar = participateBtn.dataset.userAvatar || "";
      const userUrl = participateBtn.dataset.userUrl || `#`;

      participateBtn.addEventListener("click", async function(e) {
        e.preventDefault();
        if (!actionUrl || !userId) return;

        try {
          const response = await fetch(actionUrl, {
            method: "POST",
            headers: {
              "X-CSRFToken": window.getCookie ? window.getCookie("csrftoken") : "",
              "Content-Type": "application/json"
            },
            body: JSON.stringify({})
          });
          const data = await response.json();

          if (!response.ok || data.status !== "ok") {
            const message = data.message || "Ошибка при изменении участия";
            if (window.toast) window.toast(message, { type: 'error' });
            else alert(message);
            return;
          }

          if (data.participant) {
            participateBtn.textContent = "Отказаться от участия";

            const noParticipants = document.getElementById("no-participants");
            if (noParticipants) noParticipants.remove();

            if (!document.getElementById(`participant-${userId}`)) {
              const a = document.createElement("a");
              a.href = userUrl;
              a.id = `participant-${userId}`;
              a.innerHTML = `
                <div class="participant-item">
                  <img src="${userAvatar}" alt="Аватар" class="participant-avatar">
                  <div class="participant-info">
                    <span class="participant-name">${userName}</span>
                    <span class="participant-role">Участник</span>
                  </div>
                </div>
              `;
              participantsList.appendChild(a);
            }

            participantsCount.textContent = String(parseInt(participantsCount.textContent, 10) + 1);
          } else {
            participateBtn.textContent = "Участвовать";

            const el = document.getElementById(`participant-${userId}`);
            if (el) el.remove();

            const newCount = parseInt(participantsCount.textContent, 10) - 1;
            participantsCount.textContent = String(newCount);

            if (newCount === 0) {
              const p = document.createElement("p");
              p.id = "no-participants";
              p.textContent = "Пока нет участников";
              participantsList.appendChild(p);
            }
          }

          if (window.toast) window.toast(data.message || "Список участников обновлён", { type: 'info' });
        } catch (err) {
          console.error("Ошибка запроса:", err);
          if (window.toast) window.toast("Ошибка сети", { type: 'error' });
        }
      });
    }
  });
})();
