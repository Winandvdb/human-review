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
    var t = T[i.dataset.explain], hd = i.closest('.diagram > .head'),
        line = hd || i.closest('.adoptline'), sec = i.closest('section');
    if (!t || !line || !sec) return;
    i.dataset.hrxWired = '1';
    var id = 'hrx-' + slug(sec.id + '-' + i.dataset.explain)
             + (hd ? '-' + Array.prototype.indexOf.call(sec.querySelectorAll('.diagram'), hd.parentNode) : ''), k = 'hr-explain:' + id;
    var head = line.parentElement && line.parentElement.classList.contains('adopthead')
      ? line.parentElement : null;
    var after, pos = 'afterend', cls = '';
    if (hd) { after = hd; }
    else if (head) { after = head; if (sec.id === 'requirements') { pos = 'beforeend'; cls = ' hrx-float'; } }
    else if (line.closest('.adoptcol')) { after = sec.querySelector('.vidwrap') || line; cls = ' hrx-right'; }
    else { after = line.closest('.adoptfoot') || line; cls = ' hrx-right'; }
    var box = document.getElementById(id);
    if (!box) {
      box = document.createElement('div');
      box.id = id; box.className = 'hrx-box' + cls; box.innerHTML = render(t, sec);
      after.insertAdjacentElement(pos, box);
    }
    var on = getOn(k);
    box.hidden = !on; notch();
    // The panel and the folder tab holding its (i) are ONE closed SVG path, so there are
    // no stitched borders: the tab's top is a semicircle concentric with the (i), the other
    // outer corners have radius R, the join of tab and panel is concave.
    function notch() {
      if (box.hidden) return;
      var R = 8, h = 0.75, pad = 3, gap = 6, b = i.getBoundingClientRect(), r;
      // The tab ends in the panel: pull the panel up so the (i) has little room below.
      box.style.marginTop = ''; r = box.getBoundingClientRect();
      for (var n = 0; n < 4 && Math.abs(r.top - b.bottom - gap) > 0.5; n++) {   // margins may collapse
        box.style.marginTop = (parseFloat(getComputedStyle(box).marginTop) - (r.top - b.bottom - gap)) + 'px';
        r = box.getBoundingClientRect();
      }
      var Rt = b.width / 2 + pad, W = r.width, H = r.height,
          cx = b.left + b.width / 2 - r.left, cy = b.top + b.height / 2 - r.top,
          flush = Math.abs(cx + Rt - (W - h)) < 3;
      if (flush) cx = W - h - Rt;
      var x0 = cx - Rt, x1 = cx + Rt, top = cy - Rt;
      var svg = box.querySelector(':scope > .hrx-outline');
      if (!svg) {
        svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('class', 'hrx-outline'); svg.setAttribute('aria-hidden', 'true');
        svg.appendChild(document.createElementNS('http://www.w3.org/2000/svg', 'path'));
        box.insertBefore(svg, box.firstChild);
      }
      var d = ['M', R + h, h, 'H', x0 - R, 'A', R, R, 0, 0, 0, x0, h - R,      // concave join
               'V', cy, 'A', Rt, Rt, 0, 0, 1, x1, cy];                         // round top
      if (flush) d.push('V', H - R - h);
      else d.push('V', h - R, 'A', R, R, 0, 0, 0, x1 + R, h, 'H', W - R - h,
                  'A', R, R, 0, 0, 1, W - h, R + h, 'V', H - R - h);
      d.push('A', R, R, 0, 0, 1, W - R - h, H - h, 'H', R + h, 'A', R, R, 0, 0, 1, h, H - R - h,
             'V', R + h, 'A', R, R, 0, 0, 1, R + h, h, 'Z');
      svg.setAttribute('width', W); svg.setAttribute('height', H);
      svg.firstChild.setAttribute('d', d.join(' '));
      box.classList.add('hrx-tabbed');
    }
    window.addEventListener('resize', notch);
    if (window.ResizeObserver) new ResizeObserver(notch).observe(box);
    i.setAttribute('aria-controls', id);
    i.setAttribute('aria-pressed', on ? 'true' : 'false');
    i.addEventListener('click', function (ev) {
      ev.preventDefault(); ev.stopPropagation();
      var now = i.getAttribute('aria-pressed') !== 'true';
      i.setAttribute('aria-pressed', now ? 'true' : 'false');
      box.hidden = !now; setOn(k, now); notch();
      if (now && !head) { try { box.scrollIntoView({block: 'nearest', behavior: 'smooth'}); } catch (e) {} }
    });
  }
  function run() { document.querySelectorAll('button.hrx-i[data-explain]').forEach(wire); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run);
  else run();
})();
