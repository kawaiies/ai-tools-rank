# -*- coding: utf-8 -*-
"""AI 工具榜数据源：抓 OpenRouter 模型列表 -> data/models.json"""
import json, time, urllib.request, sys, os

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "data", "models.json")

def fetch_models():
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/models",
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def normalize(data):
    """提取榜单所需字段"""
    out = []
    for m in data.get("data", []):
        mid = m.get("id", "")
        pricing = m.get("pricing", {})
        # 提取厂商: openai/gpt-4o -> openai
        vendor = mid.split("/")[0] if "/" in mid else "other"
        out.append({
            "id": mid,
            "name": mid.split("/")[-1],
            "vendor": vendor,
            "prompt_price": float(pricing.get("prompt", 0) or 0),       # $/token
            "completion_price": float(pricing.get("completion", 0) or 0),  # $/token
            "context": m.get("context_length") or 0,
            "modality": m.get("architecture", {}).get("modality", []),
            "created": m.get("created"),
            "description": (m.get("description") or "")[:200],
        })
    return out

def main():
    print("抓取 OpenRouter 模型列表...")
    data = fetch_models()
    models = normalize(data)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"), "count": len(models), "models": models},
                  f, ensure_ascii=False, indent=1)
    vendors = sorted({m["vendor"] for m in models})
    print(f"✅ {len(models)} 个模型 -> {OUT}")
    print(f"   厂商数: {len(vendors)}: {', '.join(vendors[:15])}{'...' if len(vendors)>15 else ''}")
    free = sum(1 for m in models if m["prompt_price"] == 0 and m["completion_price"] == 0)
    print(f"   免费模型: {free} 个")
    top = sorted(models, key=lambda m: m["context"], reverse=True)[:3]
    print("   最大上下文:", [(m["id"], m["context"]) for m in top])

if __name__ == "__main__":
    main()
