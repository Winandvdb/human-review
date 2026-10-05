// Film script: Owners grid with server-side paging, page size, Name/City sorting, last-name search, failure + retry.
// Screens are derived from the diff at film time (TypeScript AST), never listed by hand.
const fs = require("fs");
const path = require("path");
const {execSync} = require("child_process");

const sh = cmd => execSync(cmd, {encoding: "utf8", stdio: ["ignore", "pipe", "ignore"]}).trim();

function loadTs() {
  for (const p of [undefined, ...(process.env.NODE_PATH || "").split(path.delimiter).filter(Boolean)]) {
    try { return p ? require(require.resolve("typescript", {paths: [p]})) : require("typescript"); } catch (e) { /* next */ }
  }
  throw new Error("typescript compiler not found on NODE_PATH");
}

function walk(dir, out = []) {
  for (const f of fs.readdirSync(dir, {withFileTypes: true})) {
    const p = path.join(dir, f.name);
    if (f.isDirectory()) walk(p, out); else if (p.endsWith(".ts") && !p.endsWith(".spec.ts")) out.push(p);
  }
  return out;
}

// changed components -> every routed ancestor (climbing PAST routed ones), by template containment
function deriveScreens() {
  const ts = loadTs();
  const root = sh("git rev-parse --show-toplevel");
  const appDir = path.join(root, "petclinic-frontend/src/app");
  let base = "origin/main";
  try { base = JSON.parse(fs.readFileSync(path.join(root, "human-review.json"), "utf8")).base || base; } catch (e) { /* default */ }
  const changed = new Set(sh(`git diff --name-only $(git merge-base ${base} HEAD)`).split("\n")
    .filter(f => f.startsWith("petclinic-frontend/src/app/")).map(f => path.join(root, f)));

  const comps = {};   // class name -> {file, selector, template}
  const routes = [];  // {path, component}
  for (const file of walk(appDir)) {
    const sf = ts.createSourceFile(file, fs.readFileSync(file, "utf8"), ts.ScriptTarget.Latest, true);
    const visit = node => {
      if (ts.isClassDeclaration(node) && node.name) {
        for (const d of (ts.getDecorators ? ts.getDecorators(node) || [] : node.decorators || [])) {
          const call = d.expression;
          if (!ts.isCallExpression(call) || call.expression.getText() !== "Component") continue;
          const arg = call.arguments[0];
          const info = {file, selector: null, template: ""};
          for (const p of arg.properties) {
            const key = p.name && p.name.getText();
            if (key === "selector") info.selector = p.initializer.text;
            if (key === "templateUrl") info.template = fs.readFileSync(path.join(path.dirname(file), p.initializer.text), "utf8");
            if (key === "template") info.template = p.initializer.text || "";
          }
          info.templateFile = info.template && arg.properties.some(p => p.name.getText() === "templateUrl")
            ? path.join(path.dirname(file), arg.properties.find(p => p.name.getText() === "templateUrl").initializer.text) : null;
          comps[node.name.text] = info;
        }
      }
      if (ts.isObjectLiteralExpression(node)) {
        const props = Object.fromEntries(node.properties.filter(p => p.name).map(p => [p.name.getText(), p.initializer]));
        if (props.path && ts.isStringLiteral(props.path) && props.component) routes.push({path: props.path.text, component: props.component.getText()});
      }
      ts.forEachChild(node, visit);
    };
    visit(sf);
  }
  if (!Object.keys(comps).length || !routes.length) throw new Error("route derivation found no components/routes");

  const touched = name => {
    const c = comps[name];
    return changed.has(c.file) || (c.templateFile && changed.has(c.templateFile))
      || changed.has(c.file.replace(/\.ts$/, ".css"));
  };
  const parentsOf = name => Object.keys(comps).filter(p => comps[name].selector
    && new RegExp(`<${comps[name].selector}[\\s>/]`).test(comps[p].template));
  const affected = new Set();
  const climb = name => { if (affected.has(name)) return; affected.add(name); parentsOf(name).forEach(climb); };
  Object.keys(comps).filter(touched).forEach(climb);

  return routes.filter(r => affected.has(r.component)).map(r => ({route: "/" + r.path, component: r.component}));
}

module.exports = async ({page, say, pause, get, app, apiUrl}) => {
  const visited = [], missed = [], notFilmable = [];
  const API = /\/api\/owners\?/;

  const rows = page.locator("#ownersTable td.ownerFullName");
  const paginator = page.locator("mat-paginator");
  const rangeLabel = page.locator("mat-paginator .mat-mdc-paginator-range-label");
  const nameHeader = page.locator('#ownersTable th[mat-sort-header="name"]');
  const cityHeader = page.locator('#ownersTable th[mat-sort-header="city"]');
  const nextBtn = page.locator("mat-paginator button.mat-mdc-paginator-navigation-next");
  const findBtn = page.locator("#search-owner-form button[type=submit]");
  const lastName = page.locator("#lastName");
  const errorBox = page.locator("#ownersError");
  const retryBtn = page.locator("#retryOwners");

  const range = async () => (await rangeLabel.innerText()).trim();
  const firstRow = async () => (await rows.first().innerText()).trim();
  const settled = () => page.waitForFunction(() => {
    const t = document.querySelector("#ownersTable");
    return t && t.getAttribute("aria-busy") !== "true" && t.querySelector("td.ownerFullName");
  }, null, {timeout: 10000});
  // click, then wait until the first row differs and the grid stopped loading
  const clickAndSettle = async el => {
    const before = await firstRow();
    await el.click();
    await page.waitForFunction(b => {
      const t = document.querySelector("#ownersTable");
      const f = t && t.querySelector("td.ownerFullName");
      return t && t.getAttribute("aria-busy") !== "true" && f && f.innerText.trim() !== b;
    }, before, {timeout: 10000});
  };

  const ownersScreen = async () => {
    await page.goto(`${app}/owners`);
    await settled();
    await rangeLabel.waitFor();
    await say(`The Owners grid now loads one page at a time from the server: ${await range()}.`, paginator);
    await pause(1500);

    await nextBtn.waitFor();
    await clickAndSettle(nextBtn);
    await say(`Next asks the server for the following page: ${await range()}.`, rangeLabel);
    await pause(1200);

    const sizeSelect = page.locator("mat-paginator mat-select");
    await sizeSelect.waitFor();
    await sizeSelect.click();
    const five = page.getByRole("option", {name: "5", exact: true});
    await five.waitFor();
    await five.click();
    await page.waitForFunction(() => {
      const t = document.querySelector("#ownersTable");
      return t && t.getAttribute("aria-busy") !== "true" && t.querySelectorAll("td.ownerFullName").length === 5;
    }, null, {timeout: 10000});
    await say(`Page size is 5, 10 or 20; changing it goes back to page one: ${await range()}.`, sizeSelect);
    await pause(1500);

    await nameHeader.waitFor();
    await clickAndSettle(nameHeader);   // Name ascending is the default, one click flips it
    await say("Name sorts on the server, here descending, from page one.", nameHeader);
    await pause(1500);

    await cityHeader.waitFor();
    await clickAndSettle(cityHeader);
    await pause(600);
    await clickAndSettle(cityHeader);
    await say("City sorts the same way, ascending then descending.", cityHeader);
    await pause(1500);

    // from page two, a new search must restart at page one
    await clickAndSettle(nextBtn);
    await lastName.waitFor();
    await lastName.fill("M");
    await findBtn.click();
    await page.waitForFunction(() => {
      const t = document.querySelector("#ownersTable");
      return t && t.getAttribute("aria-busy") !== "true"
        && [...t.querySelectorAll("td.ownerFullName")].every(td => /\sM/.test(td.innerText.trim()));
    }, null, {timeout: 10000});
    const afterSearch = await range();
    if (!/^1\s/.test(afterSearch)) throw new Error(`search did not restart at page one: ${afterSearch}`);
    await say(`Searching by last name restarts at page one over the matches: ${afterSearch}.`, lastName);
    await pause(1800);

    // failure: the next page request is aborted, then let through for the retry
    await lastName.fill("");
    await findBtn.click();
    await settled();
    await page.route(API, route => route.abort("failed"));
    await nextBtn.click();
    await errorBox.waitFor();
    await say("If a page cannot be loaded, the grid gives way to an error instead of stale rows.", errorBox);
    await pause(1500);
    await page.unroute(API);
    await retryBtn.waitFor();
    await retryBtn.click();
    await settled();
    await errorBox.waitFor({state: "detached"});
    await say("Try again re-asks for the same page and the grid comes back.", rows.first());
    await pause(1500);
  };

  const defaultBeat = async screen => {
    const url = screen.route.replace(/:[A-Za-z]+/g, "1");
    await page.goto(`${app}${url}`);
    const heading = page.locator("h1, h2").first();
    await heading.waitFor();
    await say("This screen embeds a changed component.", heading);
    await pause(1500);
  };

  let screens;
  try {
    screens = deriveScreens();
  } catch (e) {
    return {ok: false, note: `FAILED to reach: route derivation (${e.message.split("\n")[0]})`};
  }
  const ordered = [...screens].sort((a, b) => (b.route === "/owners") - (a.route === "/owners"));
  if (!ordered.length) return {ok: false, note: "FAILED to reach: no routed screen derived from the diff"};

  const handlers = {"/owners": ownersScreen};
  for (const screen of ordered) {
    try {
      await (handlers[screen.route] || defaultBeat)(screen);
      visited.push(screen.route);
    } catch (e) {
      missed.push(`${screen.route} (${e.message.split("\n")[0]})`);
      await page.unroute(API).catch(() => {});
    }
  }

  return {
    ok: missed.length === 0,
    note: `${visited.length}/${ordered.length} changed screens filmed`
      + (missed.length ? ` | FAILED to reach: ${missed.join("; ")}` : "")
      + (notFilmable.length ? ` | not filmable: ${notFilmable.join("; ")}` : "")
  };
};
