// Worker half of /human-review's per-test Vitest coverage, loaded with --setupFiles.
//
// The Istanbul provider keeps its counters in a plain global; this snapshots them around every
// test and writes which statements and functions the test moved, one JSON line per test. The
// statement maps (and the source map of the transpiled code they index) are written per test
// file; join.js turns the two into TypeScript lines, the way karma/plugin.js does.
import {afterAll, afterEach, beforeEach} from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const KEY = '__VITEST_COVERAGE__';
const out = process.env.HR_TESTCOV_VITEST_DIR;
let before = {};

const snapshot = () => {
  const snap = {};
  for (const [file, fc] of Object.entries(globalThis[KEY] || {})) {
    snap[file] = {s: {...fc.s}, f: {...fc.f}};
  }
  return snap;
};

const moved = (now, was = {}) =>
  Object.keys(now).filter(id => now[id] > (was[id] || 0));

const fullName = task => {
  const names = [task.name];
  for (let s = task.suite; s && s !== task.file; s = s.suite) if (s.name) names.unshift(s.name);
  return names.join(' > ');
};

beforeEach(() => {
  if (out) before = snapshot();
});

afterEach(({task}) => {
  if (!out) return;
  const hits = {}, fhits = {};
  for (const [file, fc] of Object.entries(globalThis[KEY] || {})) {
    const s = moved(fc.s, before[file]?.s);
    const f = moved(fc.f, before[file]?.f);
    if (s.length) hits[fc.path || file] = s;
    if (f.length) fhits[fc.path || file] = f;
  }
  const row = {id: fullName(task), description: task.name, file: task.file?.filepath || '',
               status: task.result?.errors?.length ? 'failed' : 'passed', hits, fhits};
  fs.mkdirSync(out, {recursive: true});
  fs.appendFileSync(path.join(out, `tests-${process.pid}.jsonl`), JSON.stringify(row) + '\n');
});

afterAll(() => {
  if (!out) return;
  const maps = {};
  for (const [file, fc] of Object.entries(globalThis[KEY] || {})) {
    maps[fc.path || file] = {statementMap: fc.statementMap, fnMap: fc.fnMap,
                             inputSourceMap: fc.inputSourceMap};
  }
  fs.mkdirSync(out, {recursive: true});
  const name = `maps-${process.pid}-${Date.now()}-${Math.floor(Math.random() * 1e6)}.json`;
  fs.writeFileSync(path.join(out, name), JSON.stringify(maps));
});
