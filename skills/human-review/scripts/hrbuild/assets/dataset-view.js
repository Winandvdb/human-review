// The Demo tab's dataset quick view: a 👁 in each fixture of the "DB Fixture:" row opens
// the rows that fixture loads, as small grids under the Running app band — so a reviewer
// sees what "green" is without reading green.sql (Victor, 7 Oct 2026). The rows were
// computed at build time from the project's own SQL (`dataset_view.py`) and sit in
// #dsv-data; nothing here talks to the app, so the view works with the app down too.
(function () {
  var src = document.getElementById('dsv-data');
  var bar = document.querySelector('.appenv');
  if (!src || !bar) return;
  var data;
  try { data = JSON.parse(src.textContent); } catch (e) { return; }
  // A table this long starts folded to its name and row count: open, it is a wall.
  var FOLD = 10;
  var panel = null, shown = null;

  function label(name) { return name ? name : 'Default'; }
  function has(name) { return Object.prototype.hasOwnProperty.call(data.sets, name); }
  function tipFor(name) {
    return name ? 'Show the rows the “' + name + '” fixture loads: the seed, with '
                  + 'its own rows highlighted'
                : 'Show the seed rows every reset starts from';
  }

  function cell(v) {
    var td = document.createElement('td');
    if (v === null || v === undefined) { td.className = 'dsv-null'; td.textContent = 'null'; }
    else {
      var s = String(v);
      td.textContent = s;
      if (s.length > 28) td.dataset.tip = s;
      if (typeof v === 'number') td.className = 'dsv-num';
    }
    return td;
  }

  function grid(t, name) {
    var rows = (data.sets[name] && data.sets[name][t.name]) || data.sets[''][t.name] || [];
    var count = (data.counts[name] && data.counts[name][t.name] !== undefined)
      ? data.counts[name][t.name] : data.counts[''][t.name];
    var marked = (data.marks[name] && data.marks[name][t.name]) || [];
    var d = document.createElement('details');
    d.className = 'dsv-t';
    // …unless the fixture added rows to it: those rows are what its eye was pressed for,
    // so the table opens scrolled to the first of them.
    d.open = count <= FOLD || marked.length > 0;
    var sum = document.createElement('summary');
    var caret = document.createElement('span');
    caret.className = 'disclose';
    var nm = document.createElement('b');
    nm.textContent = t.name;
    var n = document.createElement('span');
    n.className = 'dsv-n';
    n.textContent = count + (count === 1 ? ' row' : ' rows')
      + (marked.length ? ' · +' + marked.length : '');
    sum.append(caret, nm, n);
    var outs = Object.keys(t.fk || {});
    if (outs.length) {
      var fk = document.createElement('span');
      fk.className = 'dsv-fk';
      var to = [];
      outs.forEach(function (c) { if (to.indexOf(t.fk[c]) < 0) to.push(t.fk[c]); });
      fk.textContent = '→ ' + to.join(', ');
      fk.dataset.tip = 'Foreign keys: ' + outs.map(function (c) {
        return c + ' → ' + t.fk[c]; }).join(', ');
      sum.appendChild(fk);
    }
    d.appendChild(sum);
    // Drawn on first open: a folded 300-row table costs nothing until someone asks.
    function fill() {
      if (d.dataset.drawn) return;
      d.dataset.drawn = '1';
      var box = document.createElement('div');
      box.className = 'dsv-grid';
      var tb = document.createElement('table');
      var hr = document.createElement('tr');
      t.cols.forEach(function (c) {
        var th = document.createElement('th');
        th.textContent = c;
        if (t.fk && t.fk[c]) { th.className = 'dsv-fkcol'; th.dataset.tip = c + ' → ' + t.fk[c]; }
        hr.appendChild(th);
      });
      var head = document.createElement('thead');
      head.appendChild(hr);
      var body = document.createElement('tbody');
      rows.forEach(function (r, i) {
        var tr = document.createElement('tr');
        if (marked.indexOf(i) >= 0) tr.className = 'dsv-new';
        r.forEach(function (v) { tr.appendChild(cell(v)); });
        body.appendChild(tr);
      });
      tb.append(head, body);
      box.appendChild(tb);
      if (count > rows.length) {
        var more = document.createElement('p');
        more.className = 'dsv-more';
        more.textContent = 'first ' + rows.length + ' of ' + count;
        box.appendChild(more);
      }
      d.appendChild(box);
      // Three seed rows of context above the first new one, on a row boundary: anything
      // else leaves a sliver of half a row peeking out under the sticky header.
      var first = body.querySelector('.dsv-new'), at = first;
      for (var k = 0; at && k < 3 && at.previousElementSibling; k++) at = at.previousElementSibling;
      if (at) requestAnimationFrame(function () {
        box.scrollTop = Math.max(0, at.offsetTop - head.offsetHeight);
      });
    }
    if (d.open) fill();
    d.addEventListener('toggle', function () { if (d.open) fill(); });
    return d;
  }

  function draw(name) {
    if (!panel) {
      panel = document.createElement('div');
      panel.className = 'dsv';
      panel.id = 'dsv-panel';
      bar.insertAdjacentElement('afterend', panel);
    }
    panel.textContent = '';
    var head = document.createElement('div');
    head.className = 'dsv-head';
    var title = document.createElement('span');
    title.className = 'dsv-title';
    title.textContent = 'Data in ' + label(name);
    var lead = document.createElement('span');
    lead.className = 'dsv-lead';
    lead.textContent = name ? 'the seed plus ' + name + '.sql — its rows highlighted'
                            : 'the seed every reset starts from';
    var close = document.createElement('button');
    close.type = 'button';
    close.className = 'dsv-close';
    close.textContent = '×';
    close.dataset.tip = 'Hide the data';
    close.addEventListener('click', function () { show(null); });
    head.append(title, lead, close);
    var row = document.createElement('div');
    row.className = 'dsv-tables';
    data.tables.forEach(function (t) { row.appendChild(grid(t, name)); });
    panel.append(head, row);
  }

  function sync() {
    [].forEach.call(bar.querySelectorAll('.dsv-eye'), function (e) {
      var on = shown !== null && e.dataset.fixture === shown;
      e.classList.toggle('on', on);
      e.setAttribute('aria-expanded', on ? 'true' : 'false');
    });
  }

  function show(name) {
    if (name === null || name === undefined || !has(name)) {
      shown = null;
      if (panel) panel.hidden = true;
    } else {
      shown = name;
      draw(name);
      panel.hidden = false;
    }
    sync();
  }

  // One 👁 per fixture in the "DB Fixture:" row, after its name and before its Seed. The
  // row is the build's and never redraws, so this runs once. Only a fixture the data
  // knows gets one: an eye that opens nothing is worse than none. (It used to ride each
  // reset *button*, which the running app drew; down, the buttons went and the seed's eye
  // was left hanging alone after Start — 8 Oct 2026.)
  function eyes() {
    [].forEach.call(bar.querySelectorAll('.appenv-fx[data-fixture]'), function (fx) {
      var name = fx.dataset.fixture || '';
      if (!has(name) || fx.querySelector('.dsv-eye')) return;
      var e = document.createElement('button');
      e.type = 'button';
      e.className = 'dsv-eye';
      e.dataset.fixture = name;
      e.setAttribute('aria-label', 'Show the data in ' + label(name));
      e.setAttribute('aria-controls', 'dsv-panel');
      e.setAttribute('aria-expanded', 'false');
      e.dataset.tip = tipFor(name);
      e.textContent = '👁︎';
      var nm = fx.querySelector('.appenv-fx-name');
      if (nm) nm.insertAdjacentElement('afterend', e); else fx.appendChild(e);
    });
    sync();
  }

  bar.addEventListener('click', function (ev) {
    var e = ev.target.closest('.dsv-eye');
    if (!e) return;
    ev.stopPropagation();
    show(shown === e.dataset.fixture ? null : e.dataset.fixture);
  });
  eyes();

  // For other parts of the page (the Tests tab's fixture dots): bring up one fixture's
  // data — the Demo tab, the panel, and the panel scrolled into view.
  window.hrOpenDataset = function (name) {
    name = name || '';
    if (!has(name)) return false;
    var tab = document.querySelector('[role="tab"][aria-controls="behaviour"]');
    if (tab && tab.getAttribute('aria-selected') !== 'true') tab.click();
    show(name);
    requestAnimationFrame(function () {
      panel.scrollIntoView({behavior: 'smooth', block: 'start'});
    });
    return true;
  };
})();
