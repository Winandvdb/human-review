// Demo film for the owners paging/sorting/search-in-URL change. Every say() waits for what it claims.
module.exports = async ({page, say, pause, app}) => {
  const isOwnersApi = r => new URL(r.url()).pathname.endsWith("/api/owners") && r.request().method() === "GET";
  // `expect` names what the answer renders: the table, or the no-owners message for an empty search
  const afterOwnersLoad = async (action, expect = "#ownersTable") => {
    const [res] = await Promise.all([page.waitForResponse(isOwnersApi), action()]);
    if (!res.ok()) throw new Error(`/api/owners answered ${res.status()}`);
    await page.locator(expect).waitFor();
  };
  const url = () => decodeURIComponent(page.url());
  const expectUrl = (re, what) => {
    if (!re.test(url())) throw new Error(`${what}: URL is ${url()}`);
  };

  const rangeLabel = page.locator("#ownersTable mat-paginator .mat-mdc-paginator-range-label");
  const cityHeader = page.locator("#ownersTable th:has-text('City') button");
  const names = page.locator("#ownersTable td.ownerFullName");
  const missed = [];
  const scene = async (name, fn) => {
    try { await fn(); } catch (e) { missed.push(`${name} (${e.message.split("\n")[0]})`); }
  };

  await scene("/owners paged", async () => {
    await afterOwnersLoad(() => page.goto(`${app}/owners`));
    await rangeLabel.waitFor();
    if (!/^\s*1\s*[–-]\s*10 of \d+/.test(await rangeLabel.innerText())) throw new Error("no '1 – 10 of N'");
    await say("The owners grid is now paged on the server: ten rows, and a total.", rangeLabel);
    await pause(800);
  });

  await scene("page size 5", async () => {
    await afterOwnersLoad(async () => {
      await page.locator("#ownersTable mat-paginator mat-select").click();
      await page.locator("mat-option").filter({hasText: /^\s*5\s*$/}).click();
    });
    await page.waitForFunction(() => document.querySelectorAll("#ownersTable td.ownerFullName").length === 5);
    expectUrl(/size=5/, "size=5");
    await say("Five rows per page, and the choice is kept in the URL.", page.locator("#ownersTable mat-paginator"));
    await pause(600);
  });

  await scene("sort city", async () => {
    await cityHeader.waitFor();
    await afterOwnersLoad(() => cityHeader.click());
    expectUrl(/sort=city/, "sort=city");
    await say("Name and City are sortable; click City to sort ascending.", cityHeader);
    await pause(600);
    await afterOwnersLoad(() => cityHeader.click());
    expectUrl(/sort=city,desc/, "sort=city,desc");
    await say("Click again for descending; the arrowhead shows the direction.", cityHeader);
    await pause(600);
  });

  await scene("next page", async () => {
    const next = page.locator("button.mat-mdc-paginator-navigation-next");
    await afterOwnersLoad(() => next.click());
    expectUrl(/page=2/, "page=2");
    await say("Next page, still sorted by city.", next);
    await pause(500);
  });

  await scene("back keeps position", async () => {
    const before = url();
    await names.first().locator("a").click();
    await page.waitForURL(/\/owners\/\d+/);
    await pause(600);
    await afterOwnersLoad(() => page.goBack());
    if (url() !== before) throw new Error(`Back landed on ${url()}, expected ${before}`);
    await say("Back from an owner returns to the same page and sort.", names.first());
    await pause(600);
  });

  const search = async (text, expect) => {
    await page.locator("#lastName").fill(text);
    await afterOwnersLoad(() => page.locator('#search-owner-form button[type="submit"]').click(), expect);
  };

  await scene("search Pot", async () => {
    await search("Pot");
    await names.first().waitFor();
    expectUrl(/lastName=Pot/, "lastName=Pot");
    if (/page=/.test(url())) throw new Error("search did not reset to page 1");
    await say("Searching starts again from page one.", page.locator("#lastName"));
    await pause(800);
  });

  await scene("search Zzzz", async () => {
    await search("Zzzz", "#noOwners");
    const none = page.locator("#noOwners");
    await none.waitFor();
    await say("When nobody matches, a message and its own Add Owner button.", none);
    await pause(1000);
  });

  return {
    ok: missed.length === 0,
    note: `${8 - missed.length}/8 scenes filmed` + (missed.length ? ` | FAILED to reach: ${missed.join("; ")}` : ""),
  };
};
