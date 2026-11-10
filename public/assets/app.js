/* Client-side filtering only. No network calls, no tracking. */
(function () {
  function norm(s) { return (s || "").toLowerCase(); }
  function bind(qSel, cardSel, countSel, test) {
    var q = document.querySelector(qSel);
    var count = document.querySelector(countSel);
    if (!q) return;
    var cards = Array.prototype.slice.call(document.querySelectorAll(cardSel));
    function apply() {
      var query = norm(q.value.trim());
      var shown = 0;
      cards.forEach(function (card) {
        var ok = (!query || norm(card.getAttribute("data-name") + " " + card.textContent).indexOf(query) !== -1)
          && test(card);
        card.classList.toggle("hidden", !ok);
        if (ok) shown++;
      });
      // Hide empty category blocks in the services list.
      document.querySelectorAll(".cat-block").forEach(function (block) {
        var any = block.querySelectorAll(".card:not(.hidden)").length > 0;
        block.classList.toggle("hidden", !any);
      });
      if (count) count.textContent = "显示 " + shown + " 条";
    }
    ["input", "change"].forEach(function (ev) {
      document.querySelectorAll(".toolbar select").forEach(function (s) { s.addEventListener(ev, apply); });
      q.addEventListener(ev, apply);
    });
    apply();
  }
  function selVal(id) { var el = document.getElementById(id); return el ? el.value : ""; }
  bind("#q", ".card.svc", "#svc-count", function (c) {
    return (!selVal("f-cat") || c.getAttribute("data-cat") === selVal("f-cat"))
      && (!selVal("f-card") || c.getAttribute("data-card") === selVal("f-card"))
      && (!selVal("f-verify") || c.getAttribute("data-verify") === selVal("f-verify"));
  });
  bind("#q2", ".card.deal", "#deal-count", function (c) {
    return (!selVal("f-dcat") || c.getAttribute("data-cat") === selVal("f-dcat"))
      && (!selVal("f-dsrc") || c.getAttribute("data-src") === selVal("f-dsrc"));
  });
})();
