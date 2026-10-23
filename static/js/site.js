(function () {
  var toggle = document.getElementById("menu-toggle");
  var menu = document.getElementById("mobile-menu");
  var iconOpen = document.getElementById("icon-open");
  var iconClose = document.getElementById("icon-close");
  if (!toggle || !menu) return;

  toggle.addEventListener("click", function () {
    var open = menu.classList.toggle("open");
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    toggle.setAttribute("aria-label", open ? "Close Menu" : "Open Menu");
    if (iconOpen) iconOpen.hidden = open;
    if (iconClose) iconClose.hidden = !open;
  });

  menu.querySelectorAll("a").forEach(function (link) {
    link.addEventListener("click", function () {
      menu.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
      toggle.setAttribute("aria-label", "Open Menu");
      if (iconOpen) iconOpen.hidden = false;
      if (iconClose) iconClose.hidden = true;
    });
  });
})();
