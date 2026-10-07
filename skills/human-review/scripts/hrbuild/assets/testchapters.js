// The Tests tab's card, read by kind of test rather than by requirement sentence.
//
// The card used to list each test under the ticket sentence it was paired with. That
// pairing is a reading (a script's or a model's) and it moved between runs, so the card's
// shape moved with it (Victor, 7 Oct 2026: "flaky, unstable, opinionated"). What a test IS
// does not move: E2E, API or unit. So the rows go into three collapsible chapters, headed
// by the same badge each row already wears; the pairing still paints the ticket on the
// left and still lights the rows a sentence click picks, it just no longer files them.
//
// The chapters replace the E2E/API/UNIT filter checkboxes: a chapter that is closed is the
// filter. In their place, one checkbox: "All tests". Off, the card lists what it always
// did by default. On, it also lists what used to sit behind the fold buttons, and every
// other test the coverage run executed (`#rm-all-tests`, written by tests.py
// `all_tests_inventory`): name, badge and file link only - no preview to open, so the
// arrow's slot stays blank and the columns stay put. Those rows are built on the first
// check, not at load: a big repo runs thousands of tests and nobody asked for them yet.
//
// The renderer (reqmap.js) is left to draw the rows; this moves them, after the fact, the
// same way trace.js and seqlink.js decorate them from the outside.
(function () {
  var map = document.querySelector('.reqmap');
  if (!map) return;
  var list = map.querySelector('.rm-code .rm-list');
  if (!list || list.querySelector('.rm-ch')) return;
  var D = {};
  try { D = JSON.parse(map.querySelector('.rm-data').textContent); } catch (e) { D = {}; }
  var TESTS = D.tests || {}, LABEL = D.cats || {e2e: 'E2E', api: 'API', unit: 'Unit'};
  // The subtitles, as few words as say what the badge alone does not.
  var CH = [['e2e', 'end-to-end, from the browser'],
            ['api', 'calling the API directly'],
            ['unit', 'one component, isolated']];
  // Which chapters start open. All three: closed, the card is three lines and a lot of
  // empty frame at 1152x625 - the reader opens the tab to see tests, so they are shown.
  var OPEN = {e2e: 1, api: 1, unit: 1};

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c];
    });
  }
  // reqmap.js's own unpacking of an identifier into words, so an added row reads like
  // the rows around it.
  function human(name) {
    name = String(name || '');
    if (/\s/.test(name)) return name;
    var w = name.replace(/[_\-]+/g, ' ')
      .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
      .replace(/([A-Z]+)([A-Z][a-z])/g, '$1 $2')
      .split(/\s+/).filter(Boolean)
      .map(function (x) { return /^[A-Z0-9]{2,}$/.test(x) ? x : x.toLowerCase(); });
    return w.length ? w[0].charAt(0).toUpperCase() + w[0].slice(1)
      + (w.length > 1 ? ' ' + w.slice(1).join(' ') : '') : name;
  }
  // `OwnerListTest.java` -> `.java`, `add-visit.component.spec.ts` -> `.spec.ts`: the
  // same face the card's own file links wear.
  function ext(file) {
    var m = /((?:\.(?:spec|test|e2e-spec|e2e|cy|it))?\.[A-Za-z0-9]+)$/i.exec(file || '');
    return m ? m[1] : (file || '');
  }
  function catOf(row) {
    var b = row.querySelector('.rm-thead .rm-cat');
    return (b && b.dataset.cat) || 'unit';
  }

  // ---- the chapters --------------------------------------------------------------------
  var chapters = {};
  CH.forEach(function (c) {
    var sec = document.createElement('section');
    sec.className = 'rm-ch';
    sec.dataset.cat = c[0];
    sec.dataset.open = OPEN[c[0]] ? 'yes' : 'no';
    sec.innerHTML = '<div class="rm-chh" role="button" tabindex="0" aria-expanded="'
      + (OPEN[c[0]] ? 'true' : 'false') + '">'
      + '<span class="rm-cat" data-cat="' + c[0] + '">' + esc(LABEL[c[0]] || c[0]) + '</span>'
      + '<span class="rm-chev" aria-hidden="true">&#9654;</span>'
      + '<span class="rm-chsub">' + esc(c[1]) + '</span>'
      + '<span class="rm-chn"></span></div>'
      + '<div class="rm-chb"><div class="rm-cho"></div></div>';
    chapters[c[0]] = sec;
  });

  // Stable hooks on every row, for whatever else decorates them from outside (the
  // fixture dot, the replay, the sequence link): the kind, the file, the test's own name.
  function hook(row) {
    var id = (row.dataset.id || '').replace(/@base$/, '');
    if (!row.dataset.cat) row.dataset.cat = catOf(row);
    if (id && !row.dataset.file) row.dataset.file = id.replace(/:\d+$/, '');
    var t = TESTS[row.dataset.id];
    if (t && !row.dataset.testName) row.dataset.testName = t.title || '';
  }
  Array.prototype.slice.call(list.children).forEach(function (el) {
    if (el.classList.contains('rm-t')) {
      hook(el);
      var sec = chapters[el.dataset.cat] || chapters.unit;
      var body = sec.querySelector('.rm-chb');
      body.insertBefore(el, body.querySelector('.rm-cho'));
    } else if (el.classList.contains('rm-tgroup')) {
      el.parentNode.removeChild(el);        // the sentence headings: no longer the grouping
    }
    // `.rm-fold` buttons stay in the list, hidden by the stylesheet: "All tests" is what
    // opens what they used to.
  });
  CH.forEach(function (c) { list.appendChild(chapters[c[0]]); });

  // ---- the "All tests" checkbox, on the card's own title row ---------------------------
  // Right-aligned on the "Tests covering the change set" strip, just before the changed-
  // tests counts (Victor, 7 Oct 2026): it changes what that card lists, so it sits on the
  // card. The filters it replaces stood over the card; their chips go.
  var inv = document.getElementById('rm-all-tests'), INV = null;
  var bar = map.querySelector('.rm-cats');
  if (bar) Array.prototype.forEach.call(bar.querySelectorAll('.rm-catf, .rm-allf'), function (x) {
    x.parentNode.removeChild(x);
  });
  var lab = document.createElement('label');
  lab.className = 'rm-allf';
  lab.innerHTML = '<input type="checkbox"> All tests';
  var head = map.querySelector('.rm-code > .rm-tkhead');
  if (head) head.insertBefore(lab, head.querySelector('.tledger'));
  var box = head ? lab.querySelector('input') : null;
  Array.prototype.forEach.call(list.querySelectorAll('.rm-t[data-catoff]'), function (r) {
    delete r.dataset.catoff;
  });
  var total = 0;
  if (inv) { try { total = (JSON.parse(inv.textContent).tests || []).length; } catch (e) {} }
  if (box) {
    var label = box.closest('label');
    label.setAttribute('data-tip', total
      ? 'Also list the ' + total + ' other tests that ran: name and file only'
      : 'Also list the tests folded away: pass-through, unmeasured, deleted');
  }

  function otherRow(t) {
    var file = t.file || '', cat = CH.some(function (c) { return c[0] === t.cat; }) ? t.cat : 'unit';
    var link = t.href
      ? '<a class="rm-tw srcref" href="' + esc(t.href) + '" data-tip="' + esc(file + ':' + t.line)
        + ' — Open in VS Code" target="_blank" rel="noopener" data-ext-only="">'
        + esc(ext(file.split('/').pop())) + '</a>'
      : '<span class="rm-tw"></span>';
    return '<div class="rm-t rm-other" data-shut="yes" data-open="no" data-cat="' + cat
      + '" data-file="' + esc(file) + '" data-test-name="' + esc(t.title) + '">'
      + '<div class="rm-thead">'
      + '<button class="rm-link" type="button" disabled tabindex="-1" aria-hidden="true"></button>'
      + '<span class="rm-cat" data-cat="' + cat + '">' + esc(LABEL[cat] || cat) + '</span>'
      + '<span class="rm-chev" aria-hidden="true">&#9654;</span>'
      + '<span class="rm-tt">' + esc(human(t.title)) + '</span>'
      + link
      + '<span class="rm-run" aria-hidden="true"></span>'
      + '<span class="rm-st rm-st-none" aria-hidden="true"></span></div></div>';
  }
  function buildOthers() {
    if (INV || !inv) return;
    try { INV = JSON.parse(inv.textContent).tests || []; } catch (e) { INV = []; }
    var html = {};
    INV.forEach(function (t) {
      var c = chapters[t.cat] ? t.cat : 'unit';
      html[c] = (html[c] || '') + otherRow(t);
    });
    Object.keys(html).forEach(function (c) {
      chapters[c].querySelector('.rm-cho').innerHTML = html[c];
    });
  }

  function folded(row) {
    return row.dataset.fold === 'yes' || row.dataset.own === 'yes' || row.dataset.del === 'yes';
  }
  function count() {
    var all = list.dataset.all === 'yes';
    CH.forEach(function (c) {
      var sec = chapters[c[0]], n = 0;
      Array.prototype.forEach.call(sec.querySelectorAll('.rm-t'), function (r) {
        if (r.classList.contains('rm-other') ? all : (all || !folded(r))) n++;
      });
      sec.querySelector('.rm-chn').textContent = n;
      sec.hidden = !n;
    });
  }
  function setAll(on) {
    if (on) buildOthers();
    list.dataset.all = on ? 'yes' : 'no';
    // The card title's hover says what the list is, so it follows the checkbox (tests.py
    // COVCARD_TIP / COVCARD_TIP_ALL).
    var tipEl = map.querySelector('.rm-code > .rm-tkhead .cov-head[data-tip]')
             || map.querySelector('.rm-code > .rm-tkhead .rm-who[data-tip]');
    if (tipEl) tipEl.setAttribute('data-tip', on
      ? 'All tests, as captured by a coverage probe.'
      : 'Tests that ran a changed line, as captured by a coverage probe.');
    ['unfold', 'unown', 'undel'].forEach(function (k) { list.dataset[k] = on ? 'yes' : 'no'; });
    count();
    window.dispatchEvent(new Event('resize'));       // the wires follow the rows
  }
  if (box) box.addEventListener('change', function () { setAll(box.checked); });
  setAll(!!(box && box.checked));

  // ---- open / close ---------------------------------------------------------------------
  function openCh(sec, on) {
    sec.dataset.open = on ? 'yes' : 'no';
    sec.querySelector('.rm-chh').setAttribute('aria-expanded', on ? 'true' : 'false');
  }
  list.addEventListener('click', function (e) {
    var h = e.target.closest('.rm-chh');
    if (!h) return;
    var sec = h.parentNode;
    openCh(sec, sec.dataset.open !== 'yes');
    window.dispatchEvent(new Event('resize'));
  });
  list.addEventListener('keydown', function (e) {
    var h = e.target.closest && e.target.closest('.rm-chh');
    if (!h || (e.key !== 'Enter' && e.key !== ' ')) return;
    e.preventDefault();
    openCh(h.parentNode, h.parentNode.dataset.open !== 'yes');
    window.dispatchEvent(new Event('resize'));
  });

  // A sentence picked on the left lights its tests on the right (reqmap.js `open`). A lit
  // row in a closed chapter would be lit where nobody can see it, so its chapter opens and
  // the first lit row is brought to the top of the card. Runs after the renderer's own
  // handler: it is registered later on the same element.
  function reveal() {
    if (list.dataset.sel !== 'yes') return;
    var hits = Array.prototype.filter.call(list.querySelectorAll('.rm-t[data-hit=yes]'),
      function (r) { return !folded(r) || list.dataset.all === 'yes'; });
    if (!hits.length) return;
    hits.forEach(function (r) { var s = r.closest('.rm-ch'); if (s) openCh(s, true); });
    var top = hits[0].getBoundingClientRect().top - list.getBoundingClientRect().top;
    if (top < 0 || top > list.clientHeight - 30) list.scrollTop += top - 4;
    window.dispatchEvent(new Event('resize'));
  }
  map.addEventListener('click', function (e) { if (e.target.closest('.rm-f')) reveal(); });
  map.addEventListener('keydown', function (e) {
    if ((e.key === 'Enter' || e.key === ' ') && e.target.closest && e.target.closest('.rm-f')) reveal();
  });
})();
