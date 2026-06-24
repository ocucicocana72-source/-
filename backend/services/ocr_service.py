"""支付宝持仓截图识别服务 — 使用Claude Vision API."""

import base64
import httpx
import os
import json
import re
from typing import Optional

# Claude API配置
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"


def encode_image(image_bytes: bytes) -> str:
    """将图片编码为base64."""
    return base64.b64encode(image_bytes).decode("utf-8")


def get_media_type(filename: str) -> str:
    """根据文件名获取MIME类型."""
    ext = filename.lower().split(".")[-1]
    types = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp", "gif": "image/gif"}
    return types.get(ext, "image/jpeg")


async def recognize_portfolio(image_bytes: bytes, filename: str) -> list[dict]:
    """
    识别支付宝持仓截图，提取基金信息.

    返回格式: [{"code": "006265", "name": "红土创新新科技股票A", "buy_price": 1.2345, "shares": 1000.00, "profit_pct": 12.34}, ...]
    """
    if not CLAUDE_API_KEY:
        # 无API key时使用模拟数据（开发测试用）
        return _mock_recognize()

    base64_image = encode_image(image_bytes)
    media_type = get_media_type(filename)

    prompt = """你是一个专业的金融数据提取助手。请仔细分析这张支付宝基金持仓截图，提取所有基金的信息。

请按照以下JSON格式返回数据（只返回JSON，不要其他文字）：

```json
[
  {
    "code": "基金代码（6位数字）",
    "name": "基金名称（完整名称）",
    "buy_price": 持有成本（浮点数，如1.2345）,
    "shares": 持有份额（浮点数，如1000.00）,
    "current_nav": 最新净值（浮点数，如1.5678）,
    "profit_amount": 持有收益（浮点数，正数为盈利，负数为亏损）,
    "profit_pct": 持有收益率（百分比，如12.34表示12.34%）
  }
]
```

注意事项：
1. 基金代码通常是6位数字
2. 如果截图中没有显示某些字段，对应值设为0
3. 收益率和收益金额保留2位小数
4. 净值保留4位小数
5. 份额保留2位小数
6. 如果是支付宝的持仓页面，通常会显示：基金名称、基金代码、持有金额、持有收益、收益率等
7. 请确保提取所有可见的基金，不要遗漏"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                CLAUDE_API_URL,
                headers={
                    "x-api-key": CLAUDE_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 2000,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": media_type,
                                        "data": base64_image,
                                    },
                                },
                                {"type": "text", "text": prompt},
                            ],
                        }
                    ],
                },
            )

            if response.status_code != 200:
                print(f"Claude API error: {response.status_code} - {response.text}")
                return []

            result = response.json()
            text = result.get("content", [{}])[0].get("text", "")

            # 提取JSON部分
            json_match = re.search(r"\[[\s\S]*\]", text)
            if json_match:
                funds = json.loads(json_match.group())
                return _validate_funds(funds)
            return []

    except Exception as e:
        print(f"识别失败: {e}")
        return []


def _validate_funds(funds: list) -> list[dict]:
    """验证和清理识别结果."""
    validated = []
    for f in funds:
        code = str(f.get("code", "")).strip()
        if not code or not code.isdigit() or len(code) != 6:
            continue
        validated.append({
            "code": code,
            "name": str(f.get("name", "")).strip(),
            "buy_price": float(f.get("buy_price", 0) or 0),
            "shares": float(f.get("shares", 0) or 0),
            "current_nav": float(f.get("current_nav", 0) or 0),
            "profit_amount": float(f.get("profit_amount", 0) or 0),
            "profit_pct": float(f.get("profit_pct", 0) or 0),
        })
    return validated


def _mock_recognize() -> list[dict]:
    """模拟识别结果（开发测试用）."""
    return [
        {
            "code": "006265",
            "name": "红土创新新科技股票A",
            "buy_price": 1.2345,
            "shares": 1000.00,
            "current_nav": 1.5678,
            "profit_amount": 333.30,
            "profit_pct": 27.00,
        },
        {
            "code": "001156",
            "name": "申万菱信新能源汽车主题灵活配置混合",
            "buy_price": 0.8765,
            "shares": 2000.00,
            "current_nav": 1.1234,
            "profit_amount": 493.80,
            "profit_pct": 28.17,
        },
        {
            "code": "161725",
            "name": "招商中证白酒指数(LOF)A",
            "buy_price": 1.5432,
            "shares": 500.00,
            "current_nav": 1.8765,
            "profit_amount": 166.65,
            "profit_pct": 21.60,
        },
    ]


async def recognize_from_upload(file_content: bytes, filename: str) -> dict:
    """
    处理上传的图片文件，返回识别结果.

    返回: {"success": bool, "funds": list, "message": str}
    """
    # 验证文件类型
    allowed_types = [".jpg", ".jpeg", ".png", ".webp", ".gif"]
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_types:
        return {"success": False, "funds": [], "message": f"不支持的文件类型: {ext}"}

    # 验证文件大小（最大10MB）
    if len(file_content) > 10 * 1024 * 1024:
        return {"success": False, "funds": [], "message": "文件大小超过10MB限制"}

    # 识别
    funds = await recognize_portfolio(file_content, filename)

    if not funds:
        return {"success": False, "funds": [], "message": "未能识别出基金信息，请确保截图清晰且包含完整的持仓信息"}

    return {
        "success": True,
        "funds": funds,
        "message": f"成功识别 {len(funds)} 只基金",
    }
