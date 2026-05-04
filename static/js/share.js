function showShareMessage(text) {
  if (window.toast) {
    window.toast(`Ссылка скопирована: ${text}`, { type: "info" });
  } else {
    alert(`Ссылка скопирована: ${text}`);
  }
}

function fallbackCopyTextToClipboard(text) {
  try {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.setAttribute("readonly", "");
    textArea.style.position = "fixed";
    textArea.style.top = "-1000px";

    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    const isCopied = document.execCommand("copy");
    document.body.removeChild(textArea);

    if (!isCopied) {
      throw new Error("document.execCommand copy failed");
    }

    showShareMessage(text);
  } catch (error) {
    console.error("Ошибка копирования (fallback):", error);
    window.prompt("Скопируйте ссылку:", text);
  }
}

document.addEventListener("click", (event) => {
  const button = event.target.closest(".share-button");

  if (!button) {
    return;
  }

  event.preventDefault();

  // data-url хранит относительный адрес профиля или проекта.
  const url = button.dataset.url
    ? window.location.origin + button.dataset.url
    : window.location.href;

  navigator.clipboard
    .writeText(url)
    .then(() => showShareMessage(url))
    .catch((error) => {
      console.error("Ошибка копирования:", error);
      fallbackCopyTextToClipboard(url);
    });
});
