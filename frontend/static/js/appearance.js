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

  function theme() {
    return current("tf-theme", "light") === "dark" ? "dark" : "light";
  }

  function check(selector, value) {
    document.querySelectorAll(selector).forEach(function (el) {
      el.checked = el.value === value;
    });
  }

  function apply() {
    var accent = current("tf-accent", "yellow");
    var density = current("tf-density", "comfortable");
    var mode = theme();
    root.setAttribute("data-accent", accent);
    root.setAttribute("data-density", density);
    root.setAttribute("data-theme", mode);
    root.setAttribute("data-bs-theme", mode);
    check("[data-tf-accent-option]", accent);
    check("[data-tf-density-option]", density);
    check("[data-tf-theme-option]", mode);
  }

  document.addEventListener("change", function (event) {
    var el = event.target;
    if (el.matches("[data-tf-accent-option]")) {
      store("tf-accent", el.value);
      apply();
    } else if (el.matches("[data-tf-density-option]")) {
      store("tf-density", el.value);
      apply();
    } else if (el.matches("[data-tf-theme-option]")) {
      store("tf-theme", el.value);
      apply();
    }
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", apply);
  }
  apply();
})();
