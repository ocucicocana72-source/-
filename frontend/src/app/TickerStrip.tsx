/* 滚动行情条 — 终端风格签名元素 */
"use client";
import { useState, useEffect } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
interface Fund { code: string; name: string; nav: number | null; daily_return: number | null; one_year_return: number | null; }

export default function TickerStrip() {
  const [funds, setFunds] = useState<Fund[]>([]);
  useEffect(() => {
    fetch(`${API}/api/fund/list?type=股票型&limit=20`)
      .then(r => r.json()).then(d => setFunds(d.funds || [])).catch(() => {});
  }, []);
  if (!funds.length) return null;
  const items = [...funds, ...funds];
  return (
    <div className="w-full overflow-hidden" style={{ background: "var(--surface-card)", borderBottom: "1px solid var(--surface-border)" }}>
      <div className="flex whitespace-nowrap animate-scroll" style={{ animationDuration: "60s" }}>
        {items.map((f, i) => {
          const ret = f.daily_return;
          const isUp = (ret ?? 0) >= 0;
          return (
            <span key={`${f.code}-${i}`} className="inline-flex items-center gap-2 px-4 py-1.5 text-xs" style={{ fontFamily: "var(--font-geist-mono)" }}>
              <span style={{ color: "var(--text-muted)" }}>{f.code}</span>
              <span style={{ color: "var(--text-secondary)" }}>{f.name.slice(0, 4)}</span>
              <span style={{ color: "var(--text-primary)" }}>{f.nav?.toFixed(2) ?? "-"}</span>
              <span style={{ color: isUp ? "var(--gain)" : "var(--loss)" }}>{ret != null ? `${ret >= 0 ? "+" : ""}${ret.toFixed(2)}%` : "-"}</span>
              <span style={{ color: "var(--surface-border)" }}>│</span>
            </span>
          );
        })}
      </div>
      <style>{`@keyframes scroll{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}.animate-scroll{animation:scroll linear infinite}.animate-scroll:hover{animation-play-state:paused}`}</style>
    </div>
  );
}
