(function () {
  var bell = document.getElementById("tf-notif-bell");
  var badge = document.getElementById("tf-notif-badge");
  var list = document.getElementById("tf-notif-list");
  var markAll = document.getElementById("tf-notif-mark-all");
  if (!bell || !badge || !list) return;

  var feedUrl = bell.getAttribute("data-feed-url");

  function getCookie(name) {
    var match = document.cookie.match(new RegExp("(^|;\\s*)" + name + "=([^;]+)"));
    return match ? decodeURIComponent(match[2]) : "";
  }

  function setBadge(count) {
    if (count > 0) {
      badge.textContent = count;
      badge.classList.remove("d-none");
    } else {
      badge.textContent = "";
      badge.classList.add("d-none");
    }
    if (markAll) {
      markAll.classList.toggle("d-none", count === 0);
    }
  }

  function bindItems() {
    list.querySelectorAll("[data-notif-read-url]").forEach(function (el) {
      el.addEventListener("click", function () {
        fetch(el.getAttribute("data-notif-read-url"), {
          method: "POST",
          keepalive: true,
          headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "X-Requested-With": "XMLHttpRequest",
          },
        }).catch(function () {});
      });
    });
  }

  function refresh() {
    fetch(feedUrl, { headers: { "X-Requested-With": "XMLHttpRequest" } })
      .then(function (response) {
        return response.json();
      })
      .then(function (data) {
        setBadge(data.count);
        list.innerHTML = data.html;
        bindItems();
      })
      .catch(function () {});
  }

  bindItems();
  window.setInterval(refresh, 30000);
})();
