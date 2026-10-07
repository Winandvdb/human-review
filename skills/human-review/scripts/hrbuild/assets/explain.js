// The blue (i) beside every "Prompt to get this" pill: "what am I looking at?".
// `shared/adopt.py` emits the button (data-explain = its EXPLAIN key) and the texts as the
// `hr-explain` JSON block; this opens a short box for it. A pill on the tab's title row
// opens its box under that row; a pill at the foot of a card, under the pill. The Tests tab
// fills the window exactly, so its box floats instead of pushing the page into a scroll.
// Open or closed is remembered per box, in localStorage when the browser allows it.
(function () {
  var data = document.getElementById('hr-explain');
  if (!data) return;
  var T;
  try { T = JSON.parse(data.textContent); } catch (e) { return; }
  function getOn(k) { try { return localStorage.getItem(k) === '1'; } catch (e) { return false; } }
  function setOn(k, v) {
    try { if (v) localStorage.setItem(k, '1'); else localStorage.removeItem(k); } catch (e) {}
  }
  function slug(s) { return String(s || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''); }
  function render(t, sec) {
    var h = '<ul>', mv = t.move ? sec.querySelector(t.move) : null, lead = '', src = '';
    if (mv) {
      // The tab's own "how this was made" line moves in: a <details> keeps its summary
      // (the count in it stays the page's own), a plain line comes along as a footnote.
      var ans = mv.querySelector('.seqhow-ans');
      if (ans) lead = ans.innerHTML; else src = mv.innerHTML;
      mv.classList.add('hrx-moved-away');
    }
    if (lead) h += '<li>' + lead + '</li>';
    (t.li || []).forEach(function (l) { h += '<li>' + l + '</li>'; });
    h += '</ul>';
    if (t.ex) h += '<div class="hrx-ex">' + t.ex + '</div>';
    if (t.code) h += '<pre>' + t.code + '</pre>';
    if (src) h += '<span class="hrx-src">' + src + '</span>';
    return h;
  }
  function wire(i) {
    if (i.dataset.hrxWired) return;
    var t = T[i.dataset.explain], line = i.closest('.adoptline'), sec = i.closest('section');
    if (!t || !line || !sec) return;
    i.dataset.hrxWired = '1';
    var id = 'hrx-' + slug(sec.id + '-' + i.dataset.explain), k = 'hr-explain:' + id;
    var head = line.parentElement && line.parentElement.classList.contains('adopthead')
      ? line.parentElement : null;
    var after, pos = 'afterend', cls = '';
    if (head) { after = head; if (sec.id === 'requirements') { pos = 'beforeend'; cls = ' hrx-float'; } }
    else if (line.closest('.adoptcol')) { after = sec.querySelector('.vidwrap') || line; cls = ' hrx-right'; }
    else { after = line.closest('.adoptfoot') || line; cls = ' hrx-right'; }
    var box = document.getElementById(id);
    if (!box) {
      box = document.createElement('div');
      box.id = id; box.className = 'hrx-box' + cls; box.innerHTML = render(t, sec);
      after.insertAdjacentElement(pos, box);
    }
    var on = getOn(k);
    box.hidden = !on;
    i.setAttribute('aria-controls', id);
    i.setAttribute('aria-pressed', on ? 'true' : 'false');
    i.addEventListener('click', function (ev) {
      ev.preventDefault(); ev.stopPropagation();
      var now = i.getAttribute('aria-pressed') !== 'true';
      i.setAttribute('aria-pressed', now ? 'true' : 'false');
      box.hidden = !now; setOn(k, now);
      if (now && !head) { try { box.scrollIntoView({block: 'nearest', behavior: 'smooth'}); } catch (e) {} }
    });
  }
  function run() { document.querySelectorAll('button.hrx-i[data-explain]').forEach(wire); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run);
  else run();
})();
