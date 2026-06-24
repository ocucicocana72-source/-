"""持仓管理服务 — JSON文件存储 + CRUD."""

import json
import os
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "portfolio.json")


def _load() -> dict:
    if not os.path.exists(DATA_FILE):
        return {"holdings": [], "updated_at": ""}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict):
    data["updated_at"] = datetime.now().isoformat()
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_all_holdings() -> list[dict]:
    return _load()["holdings"]


def add_holding(code: str, name: str, buy_price: float, shares: float, buy_date: str = "") -> dict:
    data = _load()
    for h in data["holdings"]:
        if h["code"] == code:
            h["buy_price"] = buy_price
            h["shares"] = shares
            h["buy_date"] = buy_date or h.get("buy_date", "")
            _save(data)
            return h
    holding = {"code": code, "name": name, "buy_price": buy_price, "shares": shares, "buy_date": buy_date, "added_at": datetime.now().strftime("%Y-%m-%d")}
    data["holdings"].append(holding)
    _save(data)
    return holding


def remove_holding(code: str) -> bool:
    data = _load()
    before = len(data["holdings"])
    data["holdings"] = [h for h in data["holdings"] if h["code"] != code]
    if len(data["holdings"]) < before:
        _save(data)
        return True
    return False


def update_holding(code: str, **kwargs) -> dict | None:
    data = _load()
    for h in data["holdings"]:
        if h["code"] == code:
            for k, v in kwargs.items():
                if k in ("buy_price", "shares", "buy_date"):
                    h[k] = v
            _save(data)
            return h
    return None
