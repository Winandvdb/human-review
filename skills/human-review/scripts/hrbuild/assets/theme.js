(function () {
  // The reader's colour theme: Auto (the system's), Light or Dark. Set on the root element
  // here, in the head, so the first frame is already in it -- a theme applied at the foot
  // of the body is a white flash on a dark page. The choice is kept per browser; when
  // storage is blocked the button still works for this visit.
  var KEY = 'hr-theme', ORDER = ['auto', 'light', 'dark'], h = document.documentElement;
  var cur = 'auto';
  try { cur = localStorage.getItem(KEY) || 'auto'; } catch (e) { /* blocked: Auto */ }
  if (ORDER.indexOf(cur) < 0) cur = 'auto';
  function label(t) { return t.charAt(0).toUpperCase() + t.slice(1); }
  function apply() {
    if (cur === 'auto') h.removeAttribute('data-theme'); else h.setAttribute('data-theme', cur);
    var b = document.getElementById('hr-theme');
    if (b) {
      b.textContent = 'Theme: ' + label(cur);
      b.setAttribute('aria-label', 'Colour theme: ' + label(cur) + '. Click to change it.');
    }
  }
  apply();
  document.addEventListener('DOMContentLoaded', apply);
  document.addEventListener('click', function (ev) {
    var b = ev.target && ev.target.closest && ev.target.closest('#hr-theme');
    if (!b) return;
    cur = ORDER[(ORDER.indexOf(cur) + 1) % ORDER.length];
    try { localStorage.setItem(KEY, cur); } catch (e) { /* this visit only */ }
    apply();
  });
})();
