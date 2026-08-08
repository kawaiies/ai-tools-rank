// 抓取 OpenRouter Top Weekly 热度（稳定版：初始渲染 + 有限滚动）
let puppeteer, CHROME;
try {
  puppeteer = require('puppeteer');            // Actions 全量安装（含 chromium）
  CHROME = process.env.CHROME_PATH || puppeteer.executablePath();
} catch (e) {
  puppeteer = require('puppeteer-core');       // 本机：连系统 Chrome
  CHROME = process.env.CHROME_PATH || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
}
const fs = require('fs');
const path = require('path');
const OUT = path.join(__dirname, 'data', 'hot.json');

async function main() {
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: true,
    args: ['--no-sandbox', '--disable-blink-features=AutomationControlled'],
    defaultViewport: { width: 1400, height: 900 },
  });
  const page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36');
  await page.goto('https://openrouter.ai/models?order=top-weekly', { waitUntil: 'networkidle2', timeout: 60000 }).catch(() => {});
  await new Promise(r => setTimeout(r, 5000));
  // 不滚动：Top Weekly 初始渲染约 15 条

  const lines = await page.evaluate(() => document.body.innerText.split('\n'));
  const items = [];
  const NAV = /^(Models|Compare|Discover|Top Weekly|List|Table|All|Text|Image|Audio|Video|Rerank|Speech|Transcription|Embeddings|Sign Up|Dismiss|Skip)/;
  for (let i = 1; i < lines.length; i++) {
    const m = lines[i].match(/^([\d.]+)([TM])\s*tokens$/);
    if (m) {
      const name = lines[i - 1].trim();
      if (name && name.length > 3 && !NAV.test(name)) {
        const val = parseFloat(m[1]);
        items.push({
          name,
          tokens7d: m[2] === 'T' ? val * 1e12 : val * 1e6,
          display: lines[i].trim(),
        });
      }
    }
  }

  console.log('抓到:', items.length, '条');
  items.slice(0, 15).forEach(i => console.log(' ', i.name.slice(0, 50), '|', i.display));
  if (items.length >= 5) {
    fs.mkdirSync(path.dirname(OUT), { recursive: true });
    fs.writeFileSync(OUT, JSON.stringify({ fetched_at: new Date().toISOString(), items }, null, 1), 'utf-8');
    console.log('已保存:', OUT);
  } else {
    console.log('条目太少，可能是反爬或渲染问题');
  }
  await browser.close();
}
main().catch(e => { console.error('FAIL:', e.message); process.exit(1); });
