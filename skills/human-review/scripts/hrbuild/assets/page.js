(function () {
  // The redesigned page (`hrbuild/page/render.py`): the tab bar, the "More" menu that
  // takes the views that do not fit, the sentence filter of "Asked vs tested", and the
  // demo's chapters.
  var bar = document.querySelector('.np-tabs');
  if (!bar) return;
  var tabs = Array.prototype.slice.call(bar.querySelectorAll('[data-np-tab]'));
  var panels = Array.prototype.slice.call(document.querySelectorAll('[data-np-panel]'));
  var more = bar.querySelector('.np-morebtn');
  var menu = bar.querySelector('.np-moremenu');
  var views = tabs.filter(function (t) { return t.classList.contains('np-viewtab'); });
  // Old links and bookmarks name the old tabs.
  var ALIAS = { review: 'decide', behaviour: 'changed', requirements: 'asked' };

  function show(id, push) {
    id = ALIAS[id] || id;
    if (!panels.some(function (p) { return p.getAttribute('data-np-panel') === id; })) id = 'changed';
    tabs.forEach(function (t) { t.setAttribute('aria-selected', String(t.getAttribute('data-np-tab') === id)); });
    panels.forEach(function (p) { p.hidden = p.getAttribute('data-np-panel') !== id; });
    var hiddenView = views.filter(function (v) { return v.hidden && v.getAttribute('data-np-tab') === id; })[0];
    if (more) {
      more.classList.toggle('np-holds', !!hiddenView);
      more.querySelector('.np-morelabel').textContent = hiddenView ? hiddenView.textContent : 'More';
    }
    closeMenu();
    if (push && history.replaceState) history.replaceState(null, '', '#' + id);
    document.dispatchEvent(new CustomEvent('np:tab', { detail: id }));
  }

  // Only as many views as fit stay in the bar; the rest wait in "More".
  function fit() {
    if (!views.length) return;
    views.forEach(function (v) { v.hidden = false; });
    more.hidden = true;
    var i = views.length - 1;
    while (bar.scrollWidth > bar.clientWidth && i >= 0) {
      views[i].hidden = true;
      more.hidden = false;
      i--;
    }
    Array.prototype.forEach.call(menu.querySelectorAll('[data-np-menu-for]'), function (m) {
      var tab = bar.querySelector('[data-np-tab="' + m.getAttribute('data-np-menu-for') + '"]');
      m.hidden = !(tab && tab.hidden);
    });
    var current = (location.hash || '').slice(1);
    if (current) show(current, false);
  }
  function closeMenu() {
    if (!menu) return;
    menu.hidden = true;
    more.setAttribute('aria-expanded', 'false');
  }

  document.addEventListener('click', function (ev) {
    var t = ev.target.closest && ev.target.closest('[data-np-tab], [data-np-go]');
    if (t) { show(t.getAttribute('data-np-tab') || t.getAttribute('data-np-go'), true); window.scrollTo(0, 0); return; }
    if (more && ev.target.closest && ev.target.closest('.np-morebtn')) {
      menu.hidden = !menu.hidden;
      more.setAttribute('aria-expanded', String(!menu.hidden));
      return;
    }
    if (menu && !menu.hidden && !(ev.target.closest && ev.target.closest('.np-moremenu'))) closeMenu();
    var s = ev.target.closest && ev.target.closest('[data-np-sent]');
    if (s) pick(s);
    var c = ev.target.closest && ev.target.closest('[data-np-seek]');
    if (c) seek(c);
  });
  document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') closeMenu(); });
  window.addEventListener('hashchange', function () { show(location.hash.slice(1), false); });
  window.addEventListener('resize', fit);

  // Asked vs tested: one sentence at a time, its tests in front, the others faded.
  function pick(btn) {
    var id = btn.getAttribute('data-np-sent');
    var on = btn.getAttribute('aria-pressed') !== 'true';
    Array.prototype.forEach.call(document.querySelectorAll('[data-np-sent]'), function (b) {
      b.setAttribute('aria-pressed', String(on && b.getAttribute('data-np-sent') === id));
    });
    var box = document.querySelector('.np-groups');
    if (!box) return;
    box.classList.toggle('np-filtered', on);
    Array.prototype.forEach.call(box.querySelectorAll('[data-np-group]'), function (g) {
      g.classList.toggle('np-on', on && g.getAttribute('data-np-group') === id);
    });
    var hint = document.querySelector('.np-selhint');
    if (hint) hint.textContent = on ? 'Click it again to show all' : 'Click a sentence to see its tests';
  }

  // The demo: a chapter seeks the video, and the chapter playing is marked.
  var video = document.querySelector('.np-video video');
  var chapters = Array.prototype.slice.call(document.querySelectorAll('[data-np-seek]'));
  function seek(btn) {
    if (!video) return;
    video.currentTime = parseFloat(btn.getAttribute('data-np-seek')) || 0;
    var p = video.play();
    if (p && p.catch) p.catch(function () { /* autoplay refused: the seek still stands */ });
  }
  if (video) {
    video.addEventListener('timeupdate', function () {
      var now = null;
      chapters.forEach(function (c) { if (parseFloat(c.getAttribute('data-np-seek')) <= video.currentTime + 0.25) now = c; });
      chapters.forEach(function (c) { c.classList.toggle('np-now', c === now); });
    });
    document.addEventListener('np:tab', function (e) { if (e.detail !== 'changed') video.pause(); });
  }

  fit();
  show((location.hash || '').slice(1) || 'changed', false);
})();
