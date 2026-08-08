# -*- coding: utf-8 -*-
"""创建 GitHub 仓库并推送 AI 模型榜（用 git 凭据中的 token）"""
import subprocess, json, urllib.request, sys, os

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def get_token():
    p = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n",
                       capture_output=True, text=True, encoding="utf-8")
    for line in p.stdout.splitlines():
        if line.startswith("password="):
            return line[len("password="):]
    return None

def api(method, url, body=None, token=None):
    req = urllib.request.Request(url, method=method,
        data=json.dumps(body).encode() if body else None,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                 "User-Agent": "ai-tools-rank", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")

token = get_token()
if not token:
    print("FAIL: 无法获取 GitHub token"); sys.exit(1)
print(f"token 获取成功 ({len(token)} chars)")

# 创建仓库（公开）
status, resp = api("POST", "https://api.github.com/user/repos",
    {"name": "ai-tools-rank", "description": "AI 模型榜 - OpenRouter 数据驱动的模型热度与价格排行",
     "public": True, "has_issues": False, "has_wiki": False}, token)
if status in (200, 201):
    print(f"✅ 仓库已创建: {resp.get('html_url')}")
elif status == 422 and "already_exists" in str(resp):
    print("仓库已存在，继续推送")
else:
    print(f"创建仓库: HTTP {status}: {str(resp)[:200]}")
    if status != 422: sys.exit(1)

# 检查远程是否可推（测试认证）
status, resp = api("GET", "https://api.github.com/user", token=token)
print(f"认证用户: {resp.get('login', '?')} (HTTP {status})")
