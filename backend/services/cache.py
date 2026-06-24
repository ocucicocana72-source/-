"""带过期时间的内存缓存 — 避免频繁请求被封."""

import time                                                           # 时间戳


_cache: dict[str, dict] = {}                                          # 全局缓存字典


def get_cached(key: str, ttl_seconds: int = 1800):                    # 默认30分钟过期
    """获取缓存数据，过期返回 None."""
    entry = _cache.get(key)                                            # 查缓存
    if not entry:                                                      # 无缓存
        return None                                                    # 返回空
    if time.time() - entry["ts"] > ttl_seconds:                        # 已过期
        del _cache[key]                                                # 删除旧缓存
        return None                                                    # 返回空
    return entry["data"]                                               # 返回缓存数据


def set_cached(key: str, data):                                        # 写入缓存
    """存入缓存，记录时间戳."""
    _cache[key] = {"data": data, "ts": time.time()}                    # 存数据+时间
