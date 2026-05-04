(function () {
  function showToast(message, type = "info") {
    if (window.toast) {
      window.toast(message, { type });
    } else {
      alert(message);
    }
  }

  async function postJson(url) {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": window.getCookie ? window.getCookie("csrftoken") : "",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({}),
    });

    const data = await response.json();
    return { response, data };
  }

  function updateParticipantsCount(element, diff) {
    const currentValue = parseInt(element.textContent, 10) || 0;
    const newValue = currentValue + diff;
    element.textContent = String(newValue);
    return newValue;
  }

  document.addEventListener("DOMContentLoaded", () => {
    const completeButton = document.getElementById("complete-project-btn");

    if (completeButton) {
      completeButton.addEventListener("click", async (event) => {
        event.preventDefault();

        const actionUrl = completeButton.dataset.actionUrl;
        if (!actionUrl) {
          return;
        }

        try {
          const { response, data } = await postJson(actionUrl);

          if (!response.ok || data.status !== "ok") {
            showToast(data.message || "Ошибка при завершении проекта", "error");
            return;
          }

          const statusElement = document.querySelector(".project-status-black");
          if (statusElement && data.project_status === "closed") {
            statusElement.textContent = "Закрыт";
          }

          completeButton.remove();
          showToast(data.message || "Проект завершён");
        } catch (error) {
          console.error("Ошибка запроса:", error);
          showToast("Ошибка сети", "error");
        }
      });
    }

    const participateButton = document.getElementById("participate-btn");
    const participantsList = document.getElementById("participants-list");
    const participantsCount = document.getElementById("participants-count");

    if (!participateButton || !participantsList || !participantsCount) {
      return;
    }

    const userId = participateButton.dataset.userId || null;
    const actionUrl = participateButton.dataset.actionUrl;
    const userName = participateButton.dataset.userName || "";
    const userAvatar = participateButton.dataset.userAvatar || "";
    const userUrl = participateButton.dataset.userUrl || "#";

    participateButton.addEventListener("click", async (event) => {
      event.preventDefault();

      if (!actionUrl || !userId) {
        return;
      }

      try {
        const { response, data } = await postJson(actionUrl);

        if (!response.ok || data.status !== "ok") {
          showToast(data.message || "Ошибка при изменении участия", "error");
          return;
        }

        if (data.participant) {
          participateButton.textContent = "Отказаться от участия";

          const noParticipants = document.getElementById("no-participants");
          if (noParticipants) {
            noParticipants.remove();
          }

          if (!document.getElementById(`participant-${userId}`)) {
            const link = document.createElement("a");
            link.href = userUrl;
            link.id = `participant-${userId}`;
            link.innerHTML = `
              <div class="participant-item">
                <img src="${userAvatar}" alt="Аватар" class="participant-avatar">
                <div class="participant-info">
                  <span class="participant-name">${userName}</span>
                  <span class="participant-role">Участник</span>
                </div>
              </div>
            `;
            participantsList.appendChild(link);
          }

          updateParticipantsCount(participantsCount, 1);
        } else {
          participateButton.textContent = "Участвовать";

          const participantElement = document.getElementById(`participant-${userId}`);
          if (participantElement) {
            participantElement.remove();
          }

          const newCount = updateParticipantsCount(participantsCount, -1);

          if (newCount === 0) {
            const emptyMessage = document.createElement("p");
            emptyMessage.id = "no-participants";
            emptyMessage.textContent = "Пока нет участников";
            participantsList.appendChild(emptyMessage);
          }
        }

        showToast(data.message || "Список участников обновлён");
      } catch (error) {
        console.error("Ошибка запроса:", error);
        showToast("Ошибка сети", "error");
      }
    });
  });
})();
