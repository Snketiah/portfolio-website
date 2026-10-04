// Shared behaviour: project filter, table of contents, read time, lightbox, video autoplay.
(function () {
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---- homepage filter ----
  var pills = [].slice.call(document.querySelectorAll(".filters .pill"));
  pills.forEach(function (p) {
    p.addEventListener("click", function () {
      pills.forEach(function (x) { x.setAttribute("aria-pressed", x === p); });
      var f = p.dataset.filter;
      document.querySelectorAll(".grid[data-filterable] .card").forEach(function (c) {
        c.hidden = !(f === "all" || (" " + c.dataset.tags + " ").indexOf(" " + f + " ") > -1);
      });
    });
  });

  // ---- read time ----
  var art = document.querySelector("article");
  var rt = document.querySelector("[data-readtime]");
  if (art && rt) {
    var words = art.innerText.split(/\s+/).length;
    rt.textContent = Math.max(1, Math.round(words / 230)) + " min";
  }

  // ---- table of contents (built from article h2[id]) ----
  var toc = document.querySelector(".toc");
  if (art && toc) {
    var heads = [].slice.call(art.querySelectorAll("h2[id]"));
    heads.forEach(function (h) {
      var a = document.createElement("a");
      a.href = "#" + h.id;
      a.textContent = h.dataset.toc || h.textContent;
      toc.appendChild(a);
    });
    var links = [].slice.call(toc.querySelectorAll("a"));
    var setOn = function () {
      var y = window.scrollY + 120, cur = 0;
      heads.forEach(function (h, i) { if (h.getBoundingClientRect().top + window.scrollY <= y) cur = i; });
      links.forEach(function (l, i) { l.classList.toggle("on", i === cur); });
    };
    window.addEventListener("scroll", setOn, { passive: true });
    setOn();
  }

  // ---- videos: play only while visible; no autoplay with reduced motion ----
  var vids = [].slice.call(document.querySelectorAll("video[data-auto]"));
  vids.forEach(function (v) {
    v.muted = true; v.loop = true; v.playsInline = true;
    if (reduce) { v.controls = true; return; }
  });
  if (!reduce && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) { var p = e.target.play(); if (p && p.catch) p.catch(function () {}); }
        else e.target.pause();
      });
    }, { threshold: 0.25 });
    vids.forEach(function (v) { io.observe(v); });
  }

  // ---- lightbox for article figures, evolution images and the gallery ----
  var items = [].slice.call(document.querySelectorAll("article figure img:not(.no-zoom), .evo img, .gallery-grid a"));
  if (!items.length || !window.HTMLDialogElement) return;
  var dlg = document.createElement("dialog");
  dlg.className = "lightbox";
  dlg.innerHTML = '<div class="inner"><div><img alt=""><p></p></div></div>' +
    '<button class="close" aria-label="Close">×</button>' +
    '<button class="prev" aria-label="Previous image">‹</button><button class="next" aria-label="Next image">›</button>';
  document.body.appendChild(dlg);
  var big = dlg.querySelector("img"), cap = dlg.querySelector("p"), idx = 0;
  function src(el) { return el.tagName === "A" ? el.getAttribute("href") : (el.dataset.full || el.currentSrc || el.src); }
  function caption(el) {
    if (el.tagName === "A") return el.dataset.caption || (el.querySelector("img") || {}).alt || "";
    var f = el.closest("figure"); var fc = f && f.querySelector("figcaption");
    return el.dataset.caption || (fc && f.querySelectorAll("img").length === 1 ? fc.textContent : el.alt) || "";
  }
  function show(i) {
    idx = (i + items.length) % items.length;
    big.src = src(items[idx]); big.alt = caption(items[idx]); cap.textContent = caption(items[idx]);
  }
  items.forEach(function (el, i) {
    el.addEventListener("click", function (e) { e.preventDefault(); show(i); dlg.showModal(); });
  });
  dlg.querySelector(".close").onclick = function () { dlg.close(); };
  dlg.querySelector(".prev").onclick = function () { show(idx - 1); };
  dlg.querySelector(".next").onclick = function () { show(idx + 1); };
  dlg.addEventListener("click", function (e) { if (e.target.classList.contains("inner")) dlg.close(); });
  dlg.addEventListener("keydown", function (e) {
    if (e.key === "ArrowLeft") show(idx - 1);
    if (e.key === "ArrowRight") show(idx + 1);
  });
})();
