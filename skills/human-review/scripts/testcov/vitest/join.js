// Node half of /human-review's per-test Vitest coverage.
//
//   node join.js <dir setup.js wrote into> <project dir> > vitest-N.json
//
// Reads the per-test rows and the statement maps setup.js left, maps statement and function
// ids -> transpiled JS lines -> TypeScript lines with the provider's own source map, and prints
//   {"executable": {<abs ts path>: [lines]}, "tests": [{id, description, file, status, hits}]}
// — the shape karma/plugin.js writes, so testcov.py reads both alike. The statement-ownership
// rule (a statement owns only the lines nothing nested in it owns) is plugin.js's, copied.
'use strict';
const fs = require('fs');
const path = require('path');

const [dir, project] = process.argv.slice(2);
const tm = require(require.resolve('@jridgewell/trace-mapping', {paths: [project, process.cwd()]}));

const maps = {};
const rows = [];
for (const f of fs.readdirSync(dir)) {
  const p = path.join(dir, f);
  if (f.startsWith('maps-')) Object.assign(maps, JSON.parse(fs.readFileSync(p, 'utf8')));
  else if (f.startsWith('tests-')) {
    for (const l of fs.readFileSync(p, 'utf8').split('\n')) if (l.trim()) rows.push(JSON.parse(l));
  }
}

const orig = (traced, line, column) => {
  if (!traced) return line;
  const p = tm.originalPositionFor(traced, {line, column, bias: tm.LEAST_UPPER_BOUND});
  return p && p.line;
};

const lines = {}, fnLines = {}, executable = {};
for (const [file, fc] of Object.entries(maps)) {
  let traced = null;
  if (fc.inputSourceMap) {
    try { traced = new tm.TraceMap(fc.inputSourceMap); } catch (e) { traced = null; }
  }
  const spans = [...Object.values(fc.statementMap || {}),
                 ...Object.values(fc.fnMap || {}).map(f => f.loc).filter(Boolean)]
    .map(l => [l.start.line, l.end.line]);
  const nested = (a, b) => spans.filter(([x, y]) => x >= a && y <= b && !(x === a && y === b));
  const all = new Set();
  const byId = {};
  for (const [id, loc] of Object.entries(fc.statementMap || {})) {
    const got = new Set();
    const inner = loc.end.line > loc.start.line ? nested(loc.start.line, loc.end.line) : [];
    for (let l = loc.start.line; l <= loc.end.line; l++) {
      if (l !== loc.start.line && inner.some(([x, y]) => l >= x && l <= y)) continue;
      const o = orig(traced, l, l === loc.start.line ? loc.start.column : 0);
      if (o) got.add(o);
    }
    byId[id] = [...got];
    got.forEach(x => all.add(x));
  }
  const byFn = {};
  for (const [id, fn] of Object.entries(fc.fnMap || {})) {
    const at = (fn.decl || fn.loc || {}).start;
    if (!at || !at.line) continue;
    const o = orig(traced, at.line, at.column || 0);
    if (o) { byFn[id] = [o]; all.add(o); }
  }
  lines[file] = byId;
  fnLines[file] = byFn;
  executable[file] = [...all].sort((a, b) => a - b);
}

const join = (table, ids) => {
  const got = new Set();
  for (const id of ids) (table && table[id] || []).forEach(x => got.add(x));
  return got;
};
const tests = rows.map(r => {
  const hits = {};
  for (const file of new Set([...Object.keys(r.hits || {}), ...Object.keys(r.fhits || {})])) {
    const got = new Set([...join(lines[file], r.hits[file] || []),
                         ...join(fnLines[file], (r.fhits || {})[file] || [])]);
    if (got.size) hits[file] = [...got].sort((a, b) => a - b);
  }
  return {id: r.id, description: r.description, file: r.file, status: r.status, hits};
});
process.stdout.write(JSON.stringify({executable, tests}));
