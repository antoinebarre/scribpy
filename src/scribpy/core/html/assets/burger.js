(function () {
  "use strict";

  var STORAGE_KEY = "scribpy-nav-open";

  function getNav() { return document.getElementById("scribpy-nav"); }
  function getBtn() { return document.getElementById("scribpy-burger"); }
  function getOverlay() { return document.getElementById("scribpy-overlay"); }

  function openPanel() {
    getNav().classList.add("open");
    getBtn().classList.add("open");
    getOverlay().classList.add("visible");
    getBtn().setAttribute("aria-expanded", "true");
    try { sessionStorage.setItem(STORAGE_KEY, "1"); } catch (_) {}
  }

  function closePanel() {
    getNav().classList.remove("open");
    getBtn().classList.remove("open");
    getOverlay().classList.remove("visible");
    getBtn().setAttribute("aria-expanded", "false");
    try { sessionStorage.removeItem(STORAGE_KEY); } catch (_) {}
  }

  function togglePanel() {
    if (getNav().classList.contains("open")) {
      closePanel();
    } else {
      openPanel();
    }
  }

  function navigateTo(href) {
    closePanel();
    var target = document.getElementById(href.slice(1));
    if (target) {
      setTimeout(function () {
        target.scrollIntoView({ behavior: "smooth" });
        history.pushState(null, "", href);
      }, 260);
    }
  }

  function bindNavLinks() {
    var links = document.querySelectorAll("#scribpy-nav-list a[href^='#']");
    links.forEach(function (link) {
      link.addEventListener("click", function (e) {
        e.preventDefault();
        navigateTo(link.getAttribute("href"));
      });
    });
  }

  function restoreState() {
    try {
      if (sessionStorage.getItem(STORAGE_KEY) === "1") { openPanel(); }
    } catch (_) {}
  }

  document.addEventListener("DOMContentLoaded", function () {
    var btn = getBtn();
    var overlay = getOverlay();

    btn.addEventListener("click", togglePanel);
    overlay.addEventListener("click", closePanel);

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { closePanel(); }
    });

    bindNavLinks();
    restoreState();
  });
}());
