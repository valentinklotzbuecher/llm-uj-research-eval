#!/usr/bin/env node
// harvest-pubpub-md.js
// Crawl a PubPub community, export Markdown for each Pub via the UI,
// write a CSV manifest, with rate-limit, resume, and retry logic.

import { chromium } from 'playwright';
import fs from 'fs';
import fsp from 'fs/promises';
import path from 'path';

// ---------- CLI ----------
const args = Object.fromEntries(
  process.argv.slice(2).map((x) => {
    const [k, v] = x.split('=');
    return k.startsWith('--') ? [k.slice(2), v ?? true] : [k, v ?? true];
  })
);

const COMMUNITY = (args.community || '').replace(/\/+$/, '');
if (!COMMUNITY) {
  console.error('Error: --community is required, e.g. --community=https://unjournal.pubpub.org');
  process.exit(1);
}

const OUTDIR   = args.out || './pubpub_md';
const DELAY_MS = Number(args.delay ?? 1500);
const MAX_PAGES = Number(args.maxPages ?? 80);
const RETRIES   = Number(args.retries ?? 3);

// ---------- helpers ----------
async function ensureDir(dir) { await fsp.mkdir(dir, { recursive: true }); }
function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }
function csvEscape(val) {
  if (val == null) return '';
  const s = String(val);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}
function nowIso() { return new Date().toISOString(); }
function slugFromUrl(pubUrl) {
  const m = pubUrl.match(/\/pub\/([^/?#]+)/);
  return m ? m[1] : pubUrl.replace(/https?:\/\//, '').replace(/[^\w.-]+/g, '_');
}
async function appendManifestRow(filePath, rowObj, headerOrder) {
  const header = headerOrder.join(',');
  const row = headerOrder.map((h) => csvEscape(rowObj[h] ?? '')).join(',');
  const exists = fs.existsSync(filePath);
  if (!exists) await fsp.writeFile(filePath, header + '\n', 'utf8');
  await fsp.appendFile(filePath, row + '\n', 'utf8');
}
async function loadJson(p) {
  try { return JSON.parse(await fsp.readFile(p, 'utf8')); }
  catch { return {}; }
}
async function saveJson(p, obj) {
  await fsp.writeFile(p, JSON.stringify(obj, null, 2), 'utf8');
}

// ---------- discover pubs ----------
async function discoverPubs(page, startUrl, maxPages = 80) {
  const queue = new Set([startUrl]);
  const visited = new Set();
  const pubUrls = new Set();

  while (queue.size && visited.size < maxPages) {
    const url = [...queue][0];
    queue.delete(url);
    if (visited.has(url)) continue;
    visited.add(url);

    try {
      await page.goto(url, { waitUntil: 'domcontentloaded' });
      const links = await page.$$eval('a[href]', (as) => as.map((a) => a.href.split('#')[0]));
      for (const href of links) {
        if (!href.startsWith(startUrl)) continue;
        if (/\/pub\/[^/]+/.test(href)) pubUrls.add(href);
        queue.add(href);
      }
    } catch (e) {
      console.warn('Crawl warn:', url, e.message);
    }
  }
  return [...pubUrls].sort();
}

// ---------- export via UI ----------
async function openDownloadMenu(page) {
  const candidates = [
    'button:has-text("Download")',
    'text=Download',
    '[data-test="download"]',
    'button[aria-label*="Download"]',
    'button[title*="Download"]',
  ];
  for (const sel of candidates) {
    const el = await page.$(sel);
    if (el) { await el.click().catch(() => {}); await page.waitForTimeout(300); return true; }
  }
  return false;
}

async function clickMenuItem(page, text) {
  const sel = `a:has-text("${text}"), button:has-text("${text}"), [role="menuitem"]:has-text("${text}"), text=${text}`;
  const el = await page.$(sel);
  if (!el) throw new Error(`Menu item not found: ${text}`);
  await el.click();
}

async function exportMarkdown(page, pubUrl, mdPath, retries) {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      await page.goto(pubUrl, { waitUntil: 'domcontentloaded' });
      const opened = await openDownloadMenu(page);
      if (!opened) throw new Error('Download menu not found');

      // Try “Markdown” first, then “MD”
      let download;
      try {
        [download] = await Promise.all([
          page.waitForEvent('download', { timeout: 90_000 }),
          clickMenuItem(page, 'Markdown'),
        ]);
      } catch {
        [download] = await Promise.all([
          page.waitForEvent('download', { timeout: 90_000 }),
          clickMenuItem(page, 'MD'),
        ]);
      }
      await download.saveAs(mdPath);
      return { ok: true, path: mdPath };
    } catch (e) {
      const terminal = attempt === retries;
      console.warn(`Export MD failed (attempt ${attempt}/${retries}) for ${pubUrl}: ${e.message}`);
      if (terminal) return { ok: false, error: e.message };
      await sleep(1500 + attempt * 500);
    }
  }
}

// ---------- main ----------
(async () => {
  await ensureDir(OUTDIR);
  const manifestPath = path.join(OUTDIR, 'manifest.csv');
  const statePath = path.join(OUTDIR, 'state.json');

  const header = ['timestamp', 'title', 'slug', 'pub_url', 'md_path', 'md_status', 'notes'];
  const state = await loadJson(statePath);
  state.completed ||= {};
  state.failed ||= {};

  const browser = await chromium.launch(); // set { headless: false } to watch it
  const page = await browser.newPage();

  console.log('Discovering Pub pages...');
  const pubUrls = await discoverPubs(page, COMMUNITY, MAX_PAGES);
  console.log(`Found ${pubUrls.length} Pubs`);

  for (const pubUrl of pubUrls) {
    const slug = slugFromUrl(pubUrl);
    if (state.completed[slug]) { console.log(`Skip (state): ${slug}`); continue; }

    try {
      await page.goto(pubUrl, { waitUntil: 'domcontentloaded' });
      const title = (await page.title())?.trim() || slug;

      const mdPath = path.join(OUTDIR, `${slug}.md`);
      let mdRes;
      if (fs.existsSync(mdPath)) {
        mdRes = { ok: true, path: mdPath, skipped: true };
      } else {
        mdRes = await exportMarkdown(page, pubUrl, mdPath, RETRIES);
      }

      const row = {
        timestamp: nowIso(),
        title, slug, pub_url: pubUrl,
        md_path: mdRes.ok ? (mdRes.path || '') : '',
        md_status: mdRes.ok ? (mdRes.skipped ? 'exists' : 'ok') : `fail: ${mdRes.error || 'unknown'}`,
        notes: '',
      };
      await appendManifestRow(manifestPath, row, header);

      if (mdRes.ok) {
        state.completed[slug] = true;
        delete state.failed[slug];
      } else {
        state.failed[slug] = 'markdown export failed';
      }
      await saveJson(statePath, state);
      await sleep(DELAY_MS);
    } catch (e) {
      console.warn(`Failed for ${slug}:`, e.message);
      state.failed[slug] = e.message || 'unknown';
      await saveJson(statePath, state);
      await sleep(DELAY_MS);
    }
  }

  await browser.close();
  console.log('Done.');
})();

