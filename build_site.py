# -*- coding: utf-8 -*-
"""AI 模型榜站点生成器: data/models.json -> index.html（单文件静态站）"""
import json, os, sys, re

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.abspath(__file__))

def fmt_price(p):
    """$/token -> $/M tokens 显示"""
    return f"${p * 1_000_000:.2f}/M" if p > 0 else "免费"

def fmt_context(c):
    return f"{c/1000:.0f}K" if c >= 1000 else str(c)

def build():
    with open(os.path.join(BASE, "data", "models.json"), encoding="utf-8") as f:
        data = json.load(f)
    models = data["models"]
    vendors = sorted({m["vendor"] for m in models})

    # 合并热度数据（hot.json，Top Weekly 7天 token 用量）
    hot_map = {}
    hot_path = os.path.join(BASE, "data", "hot.json")
    if os.path.exists(hot_path):
        with open(hot_path, encoding="utf-8") as f:
            hot = json.load(f)
        def norm(s):
            return re.sub(r"[^a-z0-9]", "", s.lower())
        for item in hot.get("items", []):
            key = norm(item["name"].split(":")[-1].strip())
            hot_map[key] = item
        # 同时用 model id 片段匹配
        print(f"热度数据: {len(hot.get('items', []))} 条")

    # 预渲染表格行（数据内联 + JS 排序）
    rows = []
    for i, m in enumerate(models, 1):
        free = m["prompt_price"] == 0 and m["completion_price"] == 0
        # 匹配热度
        key = norm(m["name"])
        hot_item = hot_map.get(key)
        hot_val = hot_item["tokens7d"] if hot_item else 0
        hot_disp = hot_item["display"] if hot_item else ""
        rows.append({
            "rank": i, "id": m["id"], "name": m["name"], "vendor": m["vendor"],
            "url": f"https://openrouter.ai/{m['id']}",
            "vendor_url": f"https://openrouter.ai/{m['vendor']}",
            "prompt": fmt_price(m["prompt_price"]), "completion": fmt_price(m["completion_price"]),
            "prompt_raw": m["prompt_price"], "completion_raw": m["completion_price"],
            "context": fmt_context(m["context"]), "context_raw": m["context"],
            "free": free, "desc": m["description"][:120],
            "hot": hot_val, "hot_disp": hot_disp,
        })
    hot_count = sum(1 for r in rows if r["hot"] > 0)
    print(f"热度匹配: {hot_count}/{len(rows)}")

    rows_json = json.dumps(rows, ensure_ascii=False)
    vendors_json = json.dumps(vendors, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI 模型榜 | 实时 AI 模型热度与价格排行</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:-apple-system,'Segoe UI','Microsoft YaHei',sans-serif; background:#0a0e1a; color:#e2e8f0; }}
  .wrap {{ max-width:1100px; margin:0 auto; padding:24px 16px; }}
  header {{ display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; padding:16px 0; border-bottom:1px solid #1e293b; }}
  h1 {{ font-size:24px; color:#38bdf8; }}
  .meta {{ color:#64748b; font-size:13px; }}
  .controls {{ display:flex; gap:10px; flex-wrap:wrap; padding:14px 0; }}
  select, button {{ background:#1e293b; color:#e2e8f0; border:1px solid #334155; border-radius:8px; padding:8px 14px; font-size:14px; cursor:pointer; }}
  button:hover {{ border-color:#38bdf8; }}
  button.active {{ background:#0ea5e9; border-color:#0ea5e9; color:#fff; }}
  table {{ width:100%; border-collapse:collapse; font-size:14px; }}
  th {{ text-align:left; padding:10px 12px; color:#94a3b8; font-weight:600; border-bottom:2px solid #334155; cursor:pointer; user-select:none; white-space:nowrap; }}
  th:hover {{ color:#38bdf8; }}
  td {{ padding:10px 12px; border-bottom:1px solid #1e293b; }}
  tr:hover td {{ background:#0f172a; }}
  .rank {{ color:#64748b; width:48px; }}
  .top3 .rank {{ color:#fbbf24; font-weight:700; }}
  .name {{ font-weight:600; color:#f8fafc; }}
  .name a {{ color:#f8fafc; text-decoration:none; }}
  .name a:hover {{ color:#38bdf8; text-decoration:underline; }}
  .vendor {{ color:#38bdf8; font-size:12px; }}
  .vendor a {{ color:#38bdf8; text-decoration:none; }}
  .vendor a:hover {{ text-decoration:underline; }}
  .free {{ display:inline-block; background:#059669; color:#fff; font-size:11px; padding:2px 8px; border-radius:99px; }}
  .desc {{ color:#94a3b8; font-size:12px; max-width:300px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
  footer {{ text-align:center; color:#475569; font-size:12px; padding:24px 0 8px; }}
  @media (max-width:768px) {{ .desc {{ display:none; }} }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>🤖 AI 模型榜</h1>
    <div class="meta">数据源: OpenRouter · 共 {len(models)} 个模型 · {len(vendors)} 家厂商 · 抓取于 {data['fetched_at']}</div>
  </header>
  <div class="controls">
    <select id="vendor"><option value="">全部厂商</option></select>
    <button data-sort="hot" class="active">🔥 热度榜</button>
    <button data-sort="free">免费优先</button>
    <button data-sort="price">价格从低到高</button>
    <button data-sort="context">上下文从大到小</button>
    <button data-sort="vendor">按厂商</button>
  </div>
  <table>
    <thead><tr>
      <th>#</th><th>模型</th><th>🔥 7天用量</th><th>输入价</th><th>输出价</th><th>上下文</th><th>简介</th>
    </tr></thead>
    <tbody id="tbody"></tbody>
  </table>
  <footer>AI 工具榜 MVP · 静态生成 · 每日自动更新可接入 GitHub Actions</footer>
</div>
<script>
const DATA = {rows_json};
const VENDORS = {vendors_json};
const tbody = document.getElementById('tbody');
const sel = document.getElementById('vendor');
const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
VENDORS.forEach(v => {{ const o = document.createElement('option'); o.value = v; o.textContent = v; sel.appendChild(o); }});

let curVendor = '', curSort = 'hot';
function render() {{
  let list = DATA.filter(m => !curVendor || m.vendor === curVendor);
  if (curSort === 'hot') list = [...list].sort((a,b) => b.hot - a.hot);
  else if (curSort === 'free') list = [...list].sort((a,b) => (b.free - a.free) || (a.prompt_raw - b.prompt_raw));
  else if (curSort === 'price') list = [...list].sort((a,b) => (a.prompt_raw + a.completion_raw) - (b.prompt_raw + b.completion_raw));
  else if (curSort === 'context') list = [...list].sort((a,b) => b.context_raw - a.context_raw);
  else if (curSort === 'vendor') list = [...list].sort((a,b) => a.vendor.localeCompare(b.vendor));
  tbody.innerHTML = list.map((m,i) => `<tr class="${{i<3?'top3':''}}">
    <td class="rank">${{i+1}}</td>
    <td><div class="name"><a href="${{m.url}}" target="_blank" rel="noopener">${{m.name}}</a></div><div class="vendor"><a href="${{m.vendor_url}}" target="_blank" rel="noopener">${{m.vendor}}</a></div>${{m.free?'<span class="free">免费</span>':''}}</td>
    <td>${{m.hot_disp || '—'}}</td>
    <td>${{m.prompt}}</td><td>${{m.completion}}</td><td>${{m.context}}</td>
    <td class="desc" title="${{esc(m.desc)}}">${{m.desc}}</td>
  </tr>`).join('');
}}
sel.addEventListener('change', () => {{ curVendor = sel.value; render(); }});
document.querySelectorAll('button[data-sort]').forEach(b => b.addEventListener('click', () => {{
  document.querySelectorAll('button[data-sort]').forEach(x => x.classList.remove('active'));
  b.classList.add('active'); curSort = b.dataset.sort; render();
}}));
render();
</script>
</body>
</html>"""
    # 模板里 html_mod 需要替换为真实转义函数
    out = os.path.join(BASE, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ 已生成 {out} ({os.path.getsize(out)/1024:.0f} KB)")

if __name__ == "__main__":
    build()
