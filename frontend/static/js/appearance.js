(function () {
  var root = document.documentElement;

  function current(name, fallback) {
    try {
      return localStorage.getItem(name) || fallback;
    } catch (e) {
      return fallback;
    }
  }

  function store(name, value) {
    try {
      localStorage.setItem(name, value);
    } catch (e) {
      /* private mode etc: keep defaults */
    }
  }

  function apply() {
    var accent = current("tf-accent", "yellow");
    var density = current("tf-density", "comfortable");
    root.setAttribute("data-accent", accent);
    root.setAttribute("data-density", density);
    document.querySelectorAll("[data-tf-accent-option]").forEach(function (el) {
      el.checked = el.value === accent;
    });
    document.querySelectorAll("[data-tf-density-option]").forEach(function (el) {
      el.checked = el.value === density;
    });
  }

  document.addEventListener("change", function (event) {
    var el = event.target;
    if (el.matches("[data-tf-accent-option]")) {
      store("tf-accent", el.value);
      apply();
    } else if (el.matches("[data-tf-density-option]")) {
      store("tf-density", el.value);
      apply();
    }
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", apply);
  }
  apply();
})();
