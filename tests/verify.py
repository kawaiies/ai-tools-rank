# -*- coding: utf-8 -*-
"""AI 模型榜验证套件: 语法 + 生成 + 结构断言。npm run test 调用。"""
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        print(f"FAIL: {cmd}\n{r.stderr[:500]}")
        sys.exit(1)
    return r

def main():
    # 1. Python 语法
    run(f"{sys.executable} -m py_compile build_site.py fetch_models.py deploy_gh.py")
    print("[1] Python 语法 PASS")

    # 2. Node 语法
    run("node --check fetch_hot.js")
    print("[2] Node 语法 PASS")

    # 3. 生成站点（幂等，用现有数据）
    run(f"{sys.executable} build_site.py")
    print("[3] 站点生成 PASS")

    # 4. 结构断言
    html = open(os.path.join(BASE, "index.html"), encoding="utf-8").read()
    m = re.search(r"const DATA = (\[.*?\]);", html, re.S)
    assert m, "index.html 缺少 DATA"
    rows = json.loads(m.group(1))
    assert len(rows) >= 380, f"行数异常: {len(rows)}"
    assert all(r.get("url", "").startswith("https://openrouter.ai/") for r in rows[:100]), "url 缺失"
    assert all(r.get("vendor_url", "").startswith("https://openrouter.ai/") for r in rows[:100]), "vendor_url 缺失"
    assert "target=\"_blank\"" in html, "缺少新窗口链接模板"
    assert not any('"' in r["id"] or "<" in r["id"] for r in rows), "id 含危险字符"
    print(f"[4] 结构断言 PASS: {len(rows)} 行, 链接字段齐全, 无注入风险")

    print("\n✅ 全部通过")

if __name__ == "__main__":
    main()
