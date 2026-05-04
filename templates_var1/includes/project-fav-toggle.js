<script>
    document.addEventListener("DOMContentLoaded", () => {
        const isFavoritesPage = document.body.dataset.page === "favorites";

        document.querySelectorAll(".project-fav-icon").forEach((button) => {
            button.addEventListener("click", async (event) => {
                event.preventDefault();

                const toggleUrl = (
                    button.dataset.toggleUrl ||
                    `/projects/${button.dataset.projectId}/toggle-favorite/`
                );
                const isFavorite = button.dataset.fav === "true";

                try {
                    const response = await fetch(toggleUrl, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "X-CSRFToken": window.getCookie ? window.getCookie("csrftoken") : "",
                        },
                        body: JSON.stringify({}),
                    });

                    const data = await response.json();

                    if (!response.ok || data.status !== "ok") {
                        const message = data.message || "Ошибка при обновлении избранного";
                        if (window.toast) {
                            window.toast(message, { type: "error" });
                        } else {
                            alert(message);
                        }
                        return;
                    }

                    if (isFavoritesPage && isFavorite) {
                        const card = button.closest(".project-card");
                        if (card) {
                            card.remove();
                        }
                    } else {
                        button.classList.toggle("favorite", Boolean(data.favorited));
                        button.classList.toggle("not-favorite", !data.favorited);
                        button.dataset.fav = data.favorited ? "true" : "false";
                    }

                    if (window.toast) {
                        window.toast(data.message || "Избранное обновлено", { type: "info" });
                    }
                } catch (error) {
                    console.error("Ошибка запроса:", error);

                    if (window.toast) {
                        window.toast("Ошибка сети", { type: "error" });
                    } else {
                        alert("Ошибка сети");
                    }
                }
            });
        });
    });
</script>
