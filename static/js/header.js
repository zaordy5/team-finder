(function () {
  document.addEventListener("DOMContentLoaded", () => {
    const userMenu = document.querySelector(".user-menu");
    const sidebar = document.getElementById("userSidebar");
    const overlay = document.getElementById("sidebarOverlay");

    if (!userMenu || !sidebar || !overlay) {
      return;
    }

    function openSidebar() {
      sidebar.classList.add("show");
      overlay.classList.add("show");
    }

    function closeSidebar() {
      sidebar.classList.remove("show");
      overlay.classList.remove("show");
    }

    userMenu.addEventListener("click", (event) => {
      event.stopPropagation();
      openSidebar();
    });

    overlay.addEventListener("click", closeSidebar);

    document.addEventListener("click", (event) => {
      const isClickInside = sidebar.contains(event.target) || userMenu.contains(event.target);

      if (!isClickInside && sidebar.classList.contains("show")) {
        closeSidebar();
      }
    });
  });
})();
