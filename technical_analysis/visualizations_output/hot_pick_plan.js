
(function () {
  if (window.location.hash) {
    var el = document.getElementById(window.location.hash.slice(1));
    if (el && el.classList && el.classList.contains("index-fold") && el.open === false) el.open = true;
  }
})();
