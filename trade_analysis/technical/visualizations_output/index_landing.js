
(function () {
  function allDetails() {
    return document.querySelectorAll(".index-landing details.index-fold");
  }
  var ex = document.getElementById("index-fold-expand");
  var cl = document.getElementById("index-fold-collapse");
  if (ex) ex.addEventListener("click", function () { allDetails().forEach(function (d) { d.open = true; }); });
  if (cl) cl.addEventListener("click", function () { allDetails().forEach(function (d) { d.open = false; }); });
})();
