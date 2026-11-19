// 사용: node tests/e2e/page.spec.mjs [BASE_URL]
// BASE_URL이 없으면 로컬 정적 서버를 띄운다.
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('/opt/npm-tools/node_modules/playwright');
import { spawn } from 'node:child_process';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const read = (p) => JSON.parse(readFileSync(path.join(root, p), 'utf8'));
const manifest = read('data/manifest.json');
const stories = manifest.months.flatMap((m) => read(`data/stories-${m}.json`));
const events = manifest.months.flatMap((m) => read(`data/org-events-${m}.json`));

let base = process.argv[2];
let server;
if (!base) {
  server = spawn('python3', ['-m', 'http.server', '8787', '--bind', '127.0.0.1'], { cwd: root, stdio: 'ignore' });
  await new Promise((r) => setTimeout(r, 800));
  base = 'http://127.0.0.1:8787';
}

const results = [];
function check(name, ok, detail = '') {
  results.push(ok);
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : '  ' + detail}`);
}

const browser = await chromium.launch();
try {
  // 1. 가로 스크롤 없음 + 기본 로드
  for (const width of [400, 1280]) {
    const page = await browser.newPage({ viewport: { width, height: 900 } });
    await page.goto(`${base}/#tab=stories&period=all`, { waitUntil: 'networkidle' });
    await page.waitForSelector('[data-ready="1"]', { timeout: 15000 });
    const [sw, cw] = await page.evaluate(() => [document.documentElement.scrollWidth, document.documentElement.clientWidth]);
    check(`no horizontal scroll at ${width}px`, sw <= cw, `${sw} > ${cw}`);
    if (width === 1280) {
      const folio = await page.locator('.folio').innerText();
      check('folio shows latest issue', folio.includes(`제${manifest.latest_issue}호`), folio);
      check('folio shows story count', folio.replace(/,/g, '').includes(String(manifest.counts.stories)), folio);
    }
    await page.close();
  }

  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const open = async (hash) => {
    await page.goto(`${base}/${hash}`, { waitUntil: 'networkidle' });
    await page.waitForSelector('[data-ready="1"]', { timeout: 15000 });
  };
  const loadAll = async () => {
    // "더 보기"를 끝까지 누른다
    for (let i = 0; i < 40; i++) {
      const more = page.locator('[data-more]');
      if (!(await more.count()) || !(await more.isVisible())) break;
      await more.click();
    }
  };

  // 2. 지역 필터
  await open('#tab=stories&region=ssa&period=all');
  await loadAll();
  const regions = await page.locator('.story').evaluateAll((els) => els.map((e) => e.dataset.region));
  check('region filter: all ssa', regions.length > 0 && regions.every((r) => r === 'ssa'), `${regions.length} items`);

  // 3. 기구 필터
  await open('#tab=stories&org=WFP&period=all');
  await loadAll();
  const n = await page.locator('.story').count();
  const expected = stories.filter((s) => s.orgs.includes('WFP')).length;
  check('org filter WFP count', n === expected, `${n} vs ${expected}`);

  // 4. 빈 결과
  await open('#tab=stories&q=%EC%97%86%EB%8A%94%EB%8B%A8%EC%96%B4zzz&period=all');
  const emptyText = await page.locator('[data-empty]').innerText().catch(() => '');
  check('empty state text', emptyText.includes('해당 조건의 기사가 없습니다'), emptyText);
  check('csv disabled when empty', await page.locator('[data-csv="stories"]').isDisabled());

  // 5. 기구별 동향 탭
  await open('#tab=orgs&org=WFP&period=all');
  const tl = await page.locator('.event').count();
  const tlExpected = events.filter((e) => e.org === 'WFP' || e.also.includes('WFP')).length;
  check('org timeline count WFP', tl === tlExpected, `${tl} vs ${tlExpected}`);
  await loadAll();
  const rel = await page.locator('.story').count();
  check('org related stories count WFP', rel === expected, `${rel} vs ${expected}`);

  // 6. CSV 내용
  await open('#tab=stories&period=all');
  await loadAll();
  const csv = await page.evaluate(() => window.__csvForTest());
  check('csv starts with BOM', csv.startsWith('﻿'));
  const header = csv.slice(1).split('\n')[0].replace(/\r$/, '');
  check('csv header', header === '날짜,호,지역,국가,세부 지역,기구,주제,제목,요약,수치,미확인,출처1 제목,출처1 URL,출처2 제목,출처2 URL,출처3 제목,출처3 URL', header);
  const tricky = stories.find((s) => s.summary.includes(',') && s.summary.includes('"'));
  if (tricky) {
    const quoted = '"' + tricky.summary.replace(/"/g, '""') + '"';
    check('csv quotes tricky summary', csv.includes(quoted));
  } else {
    check('csv quotes tricky summary (no fixture, skipped)', true);
  }

  // 7. manifest 실패
  const p2 = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await p2.route('**/data/manifest.json', (r) => r.abort());
  const t0 = Date.now();
  await p2.goto(`${base}/`, { waitUntil: 'domcontentloaded' });
  const err = await p2.locator('[data-error]').innerText({ timeout: 11000 }).catch(() => '');
  check('error state within 10s', err.includes('데이터를 불러오지 못했습니다') && Date.now() - t0 < 11000, err);
  await p2.close();
} finally {
  await browser.close();
  if (server) server.kill();
}
const failed = results.filter((r) => !r).length;
console.log(`${results.length - failed}/${results.length} passed`);
process.exit(failed ? 1 : 0);
