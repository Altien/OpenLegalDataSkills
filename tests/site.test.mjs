import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const html = await readFile(new URL("../index.html", import.meta.url), "utf8");
const css = await readFile(new URL("../styles.css", import.meta.url), "utf8");
const script = await readFile(new URL("../script.js", import.meta.url), "utf8");

test("page has essential metadata and a single primary heading", () => {
  assert.match(html, /<meta name="description"/);
  assert.match(html, /<meta name="viewport"/);
  assert.equal((html.match(/<h1\b/g) ?? []).length, 1);
});

test("page contains the five published legal skills", () => {
  const pageText = html.replaceAll("&amp;", "&");
  for (const skill of ["Case law", "Citation checking", "Contract clauses", "Statutes & regulations", "World law"]) {
    assert.ok(pageText.includes(skill), `Missing skill: ${skill}`);
  }
});

test("conversion links point to the real install and account destinations", () => {
  assert.match(html, /github\.com\/Altien\/OpenLegalDataSkills/);
  assert.match(html, /openlegaldata\.net\/account/);
  assert.match(html, /\/plugin marketplace add Altien\/OpenLegalDataSkills/);
});

test("example output is honest and onboarding includes API key setup", () => {
  assert.doesNotMatch(html, /LIVE DATA/);
  assert.match(html, /ILLUSTRATIVE/);
  assert.match(html, /OPENLEGALDATA_API_KEY/);
  assert.doesNotMatch(html, /55\+ jurisdictions/);
});

test("responsive and reduced-motion styles are present", () => {
  assert.match(css, /@media \(max-width: 760px\)/);
  assert.match(css, /prefers-reduced-motion: reduce/);
});

test("interactive script supports navigation and copy affordances", () => {
  assert.match(script, /navToggle/);
  assert.match(script, /clipboard/);
});
