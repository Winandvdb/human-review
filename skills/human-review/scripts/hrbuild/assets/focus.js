// The focus chooser: every level is already in the page, so switching is a visibility
// flip, not a fetch — the guide must keep working as a single emailed file.
(function () {
  document.querySelectorAll('.diagram .focus').forEach(function (bar) {
    var diagram = bar.closest('.diagram');
    bar.addEventListener('click', function (ev) {
      var button = ev.target.closest('button[data-level]');
      if (!button) return;
      var level = button.getAttribute('data-level');
      bar.querySelectorAll('button[data-level]').forEach(function (b) {
        b.setAttribute('aria-pressed', String(b === button));
      });
      diagram.querySelectorAll('.svgbox[data-level]').forEach(function (box) {
        box.hidden = box.getAttribute('data-level') !== level;
      });
    });
  });
})();

// The morph between radii. Each radius is its own PlantUML render with its own layout, so
// a bare visibility flip throws every box somewhere new and the reader loses the change
// they were looking at. Instead: scroll so the changed entities (the ripple-1 boxes) stay
// where the eye already is, slide every box both views share from its old spot to its
// new one, ghost out the ones that left, and fade the newcomers in with a short glow —
// the one thing a wider radius exists to show is what it added. Edges are re-routed by
// every render, so they are not tracked: they fade in once the boxes have landed.
// Runs in the capture phase, ahead of the chooser above, and performs the same flip
// itself so the order of the two listeners never matters.
(function () {
  if (window.__dgmMorph) return;
  window.__dgmMorph = true;
  var MOVE = 380, GLOW = 1400;
  var motion = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;

  function svgOf(box) { return box && box.querySelector('svg'); }
  function entities(svg) {
    var out = {};
    if (!svg) return out;
    svg.querySelectorAll('g.entity[data-qualified-name]').forEach(function (g) {
      out[g.getAttribute('data-qualified-name')] = g;
    });
    return out;
  }
  // The diff's own boxes: the first ripple, or anything painted as added or removed.
  function isFocus(g) {
    var shape = g.querySelector(':scope > rect, :scope > path, :scope > polygon');
    var fill = shape ? (shape.getAttribute('fill') || '') : '';
    return /dgm-ripple-1|dgm-diff-(add|del)/.test(fill);
  }
  function rects(map) {
    var out = {};
    Object.keys(map).forEach(function (k) { out[k] = map[k].getBoundingClientRect(); });
    return out;
  }
  function centre(names, r) {
    var x = 0, y = 0;
    names.forEach(function (n) { x += r[n].left + r[n].width / 2; y += r[n].top + r[n].height / 2; });
    return { x: x / names.length, y: y / names.length };
  }
  function scroller(el) {
    for (var p = el.parentElement; p && p !== document.body; p = p.parentElement) {
      var oy = getComputedStyle(p).overflowY;
      if ((oy === 'auto' || oy === 'scroll' || oy === 'overlay') && p.scrollHeight > p.clientHeight) return p;
    }
    return document.scrollingElement || document.documentElement;
  }
  // Screen pixels to the SVG's user units: the picture is scaled down by `max-width:100%`.
  function unit(svg) {
    var vb = svg.viewBox && svg.viewBox.baseVal;
    var w = svg.getBoundingClientRect().width;
    return vb && vb.width && w ? vb.width / w : 1;
  }

  function settle(diagram) {
    var done = diagram && diagram.__dgmMorphEnd;
    if (done) done();
  }

  function morph(diagram, bar, button) {
    var level = button.getAttribute('data-level');
    var from = diagram.querySelector('.svgbox[data-level]:not([hidden])');
    var to = null;
    diagram.querySelectorAll('.svgbox[data-level]').forEach(function (b) {
      if (b.getAttribute('data-level') === level) to = b;
    });
    settle(diagram);
    if (!from || !to || from === to) return;

    var oldSvg = svgOf(from), newSvg = svgOf(to);
    var oldEnt = entities(oldSvg), oldR = rects(oldEnt), oldSvgR = oldSvg && oldSvg.getBoundingClientRect();

    // The flip itself, identical to the chooser's.
    bar.querySelectorAll('button[data-level]').forEach(function (b) {
      b.setAttribute('aria-pressed', String(b === button));
    });
    diagram.querySelectorAll('.svgbox[data-level]').forEach(function (b) {
      b.hidden = b !== to;
    });
    if (!oldSvg || !newSvg) return;

    var newEnt = entities(newSvg), newR = rects(newEnt);
    var shared = Object.keys(newEnt).filter(function (n) { return n in oldR; });
    var arrived = Object.keys(newEnt).filter(function (n) { return !(n in oldR); });
    var left = Object.keys(oldEnt).filter(function (n) { return !(n in newEnt); });

    // Anchor: keep the change where it was on screen. Only the page scrolls, so the
    // final picture is exactly the un-animated one; whatever the scroll cannot absorb
    // (the top of the page, or the chooser itself about to leave the screen) is left to
    // the slide below.
    var anchors = shared.filter(function (n) { return isFocus(newEnt[n]); });
    if (!anchors.length) anchors = shared;
    if (anchors.length) {
      var a = centre(anchors, oldR), b = centre(anchors, newR);
      var sc = scroller(to), dy = b.y - a.y;
      var top = sc === document.scrollingElement || sc === document.documentElement
        ? 0 : sc.getBoundingClientRect().top;
      // A chooser that does not pin (an older stylesheet) must not be scrolled away.
      if (dy > 0 && getComputedStyle(bar).position !== 'sticky') {
        dy = Math.min(dy, Math.max(0, bar.getBoundingClientRect().top - top - 8));
      }
      var before = sc.scrollTop;
      sc.scrollTop = before + dy;
      var dx = b.x - a.x;
      if (to.scrollWidth > to.clientWidth) to.scrollLeft += dx;
      if (sc.scrollTop !== before || dx) newR = rects(newEnt);
    }

    var still = !!(motion && motion.matches);
    var touched = [], ghost = null, timers = [];
    function end() {
      timers.forEach(clearTimeout);
      touched.forEach(function (el) {
        el.style.transition = el.style.transform = el.style.opacity = '';
        el.classList.remove('dgm-m-new', 'dgm-m-glow', 'dgm-m-in', 'dgm-m-fade');
      });
      if (ghost && ghost.parentNode) ghost.parentNode.removeChild(ghost);
      to.classList.remove('dgm-morphing');
      if (diagram.__dgmMorphEnd === end) diagram.__dgmMorphEnd = null;
    }
    diagram.__dgmMorphEnd = end;

    arrived.forEach(function (n) { touched.push(newEnt[n]); newEnt[n].classList.add('dgm-m-glow'); });
    timers.push(setTimeout(end, (still ? 0 : MOVE) + GLOW));
    if (still) return;

    to.classList.add('dgm-morphing');
    var k = unit(newSvg);
    shared.forEach(function (n) {
      var g = newEnt[n], o = oldR[n], c = newR[n];
      var tx = (o.left - c.left) * k, ty = (o.top - c.top) * k;
      if (Math.abs(tx) < 0.5 && Math.abs(ty) < 0.5) return;
      touched.push(g);
      g.style.transition = 'none';
      g.style.transform = 'translate(' + tx + 'px,' + ty + 'px)';
    });
    arrived.forEach(function (n) { newEnt[n].classList.add('dgm-m-new'); });
    // Everything that is not a box — edges, title, legend — waits for the boxes.
    Array.prototype.forEach.call(newSvg.querySelectorAll('g.link, g.title, g.footer, g.caption, g.legend, g.cluster'), function (el) {
      touched.push(el);
      el.classList.add('dgm-m-fade');
    });

    // The ones that left: a copy of the old picture, pinned where it was, showing only them.
    if (left.length && oldSvgR) {
      ghost = oldSvg.cloneNode(true);
      ghost.removeAttribute('id');
      ghost.querySelectorAll('[id]').forEach(function (el) {
        if (el.tagName.toLowerCase() !== 'filter' && el.tagName.toLowerCase() !== 'lineargradient') el.removeAttribute('id');
      });
      ghost.querySelectorAll('g.entity[data-qualified-name], g.link, g.title, g.footer, g.caption, g.legend, g.cluster').forEach(function (el) {
        var n = el.getAttribute('data-qualified-name');
        if (!n || n in newEnt || !el.classList.contains('entity')) el.style.visibility = 'hidden';
      });
      ghost.classList.add('dgm-m-ghost');
      var boxR = to.getBoundingClientRect();
      ghost.style.left = (oldSvgR.left - boxR.left - to.clientLeft + to.scrollLeft) + 'px';
      ghost.style.top = (oldSvgR.top - boxR.top - to.clientTop + to.scrollTop) + 'px';
      ghost.style.width = oldSvgR.width + 'px';
      ghost.style.height = oldSvgR.height + 'px';
      ghost.style.margin = '0';
      ghost.style.background = 'transparent';
      ghost.style.maxWidth = 'none';
      to.appendChild(ghost);
    }

    void to.offsetWidth;                                  // commit the starting frame
    requestAnimationFrame(function () {
      shared.forEach(function (n) {
        var g = newEnt[n];
        if (!g.style.transform) return;
        g.style.transition = 'transform ' + MOVE + 'ms cubic-bezier(.2,.7,.2,1)';
        g.style.transform = '';
      });
      arrived.forEach(function (n) { newEnt[n].classList.add('dgm-m-in'); });
      if (ghost) ghost.classList.add('dgm-m-out');
      timers.push(setTimeout(function () {
        newSvg.querySelectorAll('.dgm-m-fade').forEach(function (el) { el.classList.add('dgm-m-in'); });
      }, MOVE * 0.8));
    });
  }

  document.addEventListener('click', function (ev) {
    var button = ev.target && ev.target.closest && ev.target.closest('.diagram .focus button[data-level]');
    if (!button) return;
    var bar = button.closest('.focus'), diagram = button.closest('.diagram');
    try { morph(diagram, bar, button); } catch (e) { settle(diagram); }
  }, true);
})();
