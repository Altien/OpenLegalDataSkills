import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const html = await readFile(new URL("../index.html", import.meta.url), "utf8");
const css = await readFile(new URL("../styles.css", import.meta.url), "utf8");
const script = await readFile(new URL("../script.js", import.meta.url), "utf8");
const terms = await readFile(new URL("../terms.html", import.meta.url), "utf8");
const commercialLicense = await readFile(new URL("../plugins/openlegaldata/LICENSE", import.meta.url), "utf8");
const pluginManifest = JSON.parse(await readFile(new URL("../plugins/openlegaldata/.claude-plugin/plugin.json", import.meta.url), "utf8"));
const marketplace = JSON.parse(await readFile(new URL("../.claude-plugin/marketplace.json", import.meta.url), "utf8"));
const readme = await readFile(new URL("../README.md", import.meta.url), "utf8");

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

test("commercial terms are linked and reserve the platform value for Altien", () => {
  assert.match(html, /href="terms\.html"/);
  assert.match(terms, /Altien Limited/);
  assert.match(terms, /03466192/);
  assert.match(terms, /Derived Provenance Data/);
  assert.match(terms, /Customer Content remains owned by the Customer/);
  assert.match(terms, /business sale/);
  assert.match(terms, /current Software is proprietary to Altien/);
  assert.match(terms, /business sale/);
  assert.doesNotMatch(html, /Apache 2\.0|Open-source skills|skills are open source/);
});

test("version 1 skills carry Altien's subscription-based commercial licence", () => {
  assert.ok(Number(pluginManifest.version.split(".")[0]) >= 1);
  assert.equal(marketplace.metadata.version, pluginManifest.version);
  assert.match(readme, new RegExp(`Version: ${pluginManifest.version.replaceAll(".", "\\.")}`));
  assert.equal(pluginManifest.license, "LicenseRef-Altien-Commercial-1.0");
  assert.match(commercialLicense, /ALTIEN OPENLEGALDATA COMMERCIAL SOFTWARE LICENCE/);
  assert.match(commercialLicense, /active OpenLegalData subscription/);
  assert.match(commercialLicense, /business sale/);
  assert.match(commercialLicense, /earlier version/);
});
