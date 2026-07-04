/* 新闻聚合页 — 暗色终端风格 */
"use client";
import { useState, useEffect, useCallback } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
interface NewsItem { title: string; url: string; source: string; time: string; sector: string; sentiment: string; sentiment_score: number; ai_summary: string; ai_comment: string; ai_fund_advice: string; ai_risk_note: string; }

const SECTOR_COLORS: Record<string, string> = {
  "科技": "#A78BFA", "医药": "#34D399", "新能源": "#FBBF24", "消费": "#FB923C",
  "金融": "#60A5FA", "军工": "#F87171", "基建": "#9CA3AF", "农业": "#A3E635",
  "港股": "#22D3EE", "债券": "#94A3B8", "综合": "#6B7280",
};
const SENTIMENT_STYLES: Record<string, { color: string; bg: string; emoji: string }> = {
  "利好": { color: "var(--gain)", bg: "rgba(255,77,79,0.1)", emoji: "🟢" },
  "利空": { color: "var(--loss)", bg: "rgba(0,196,140,0.1)", emoji: "🔴" },
  "中性": { color: "var(--text-muted)", bg: "var(--surface-deep)", emoji: "⚪" },
};

export default function NewsPage() {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [sector, setSector] = useState("全部");
  const [sentiment, setSentiment] = useState("全部");
  const [search, setSearch] = useState("");
  const [sectors, setSectors] = useState<string[]>(["全部"]);
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  const fetchNews = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ limit: "100", sector });
      if (sentiment !== "全部") params.set("sentiment", sentiment);
      if (search) params.set("search", search);
      const res = await fetch(`${API}/api/news/?${params}`);
      const data = await res.json();
      setNews(data.news || []); if (data.sectors) setSectors(data.sectors);
    } catch {} finally { setLoading(false); }
  }, [sector, sentiment, search]);

  useEffect(() => { fetchNews(); }, [fetchNews]);

  const inputCls = "px-3 py-1.5 rounded-lg text-xs outline-none transition-colors";
  const inputStyle = { background: "var(--surface-card)", color: "var(--text-primary)", border: "1px solid var(--surface-border)" };

  return (
    <div className="min-h-screen" style={{ background: "var(--surface-deep)", color: "var(--text-primary)" }}>
      <div className="max-w-5xl mx-auto px-4 py-6">
        <header className="mb-6">
          <Link href="/" className="text-xs" style={{ color: "var(--info)" }}>← 返回首页</Link>
          <h1 className="text-xl font-bold mt-2" style={{ fontFamily: "var(--font-serif), serif" }}>📰 财经新闻聚合</h1>
          <p className="text-[10px] mt-1" style={{ color: "var(--text-muted)" }}>多源抓取 · 板块分类 · AI 智能分析 · 近7天</p>
          <div className="divider-gold" />
        </header>

        {/* 板块导航 */}
        <div className="mb-4 flex gap-2 flex-wrap">
          {sectors.map(s => (
            <button key={s} onClick={() => setSector(s)} className="px-3 py-1.5 rounded-full text-xs transition-colors"
              style={sector === s ? { background: "var(--accent)", color: "#000", fontWeight: 600 } : { background: "var(--surface-card)", color: "var(--text-secondary)", border: "1px solid var(--surface-border)" }}>
              {s}
            </button>
          ))}
        </div>

        {/* 筛选栏 */}
        <div className="mb-5 flex flex-wrap gap-2">
          {["全部", "利好", "利空", "中性"].map(s => (
            <button key={s} onClick={() => setSentiment(s)} className="px-2.5 py-1 rounded-full text-[10px] transition-colors"
              style={sentiment === s ? { background: "var(--surface-hover)", color: "var(--text-primary)" } : { background: "var(--surface-card)", color: "var(--text-muted)" }}>
              {s === "利好" ? "🟢 利好" : s === "利空" ? "🔴 利空" : s === "中性" ? "⚪ 中性" : "全部"}
            </button>
          ))}
          <div className="flex-1 min-w-[180px]">
            <input type="text" value={search} onChange={e => setSearch(e.target.value)} onKeyDown={e => e.key === "Enter" && fetchNews()}
              placeholder="搜索关键词..." className={inputCls + " w-full"} style={inputStyle} />
          </div>
          <button onClick={fetchNews} className="px-3 py-1.5 rounded-lg text-xs" style={{ background: "var(--surface-card)", color: "var(--text-secondary)", border: "1px solid var(--surface-border)" }}>🔄</button>
        </div>

        {loading ? (
          <div className="text-center py-12" style={{ color: "var(--text-muted)" }}>加载中...</div>
        ) : (
          <div className="space-y-3">
            <div className="text-[10px] mb-2" style={{ color: "var(--text-muted)" }}>共 <b style={{ color: "var(--text-primary)" }}>{news.length}</b> 条 · {sector}</div>
            {news.map((item, i) => {
              const sectorColor = SECTOR_COLORS[item.sector] || "#6B7280";
              const sent = SENTIMENT_STYLES[item.sentiment] || SENTIMENT_STYLES["中性"];
              const isExpanded = expandedIdx === i;
              return (
                <div key={i} className="rounded-lg overflow-hidden" style={{ background: "var(--surface-card)", border: "1px solid var(--surface-border)" }}>
                  <a href={item.url} target="_blank" rel="noopener noreferrer" className="block p-4 transition-colors"
                    onMouseEnter={e => (e.currentTarget.style.background = "var(--surface-hover)")}
                    onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
                  >
                    <div className="text-sm leading-relaxed" style={{ color: "var(--text-primary)" }}>{item.title}</div>
                    <div className="flex items-center gap-2 mt-2 flex-wrap">
                      <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: `${sectorColor}20`, color: sectorColor }}>{item.sector}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: sent.bg, color: sent.color }}>{sent.emoji} {item.sentiment}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: "var(--surface-deep)", color: "var(--text-muted)" }}>{item.source}</span>
                      <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>{item.time}</span>
                      <span className="text-[10px] ml-auto" style={{ fontFamily: "var(--font-geist-mono)", color: "var(--text-muted)" }}>{(item.sentiment_score * 100).toFixed(0)}分</span>
                    </div>
                  </a>
                  <button onClick={() => setExpandedIdx(isExpanded ? null : i)}
                    className="w-full px-4 py-2 text-[10px] transition-colors"
                    style={{ background: "var(--surface-deep)", color: "var(--info)", borderTop: "1px solid var(--surface-border)" }}>
                    {isExpanded ? "收起 AI 分析 ▲" : "展开 AI 分析 ▼"}
                  </button>
                  {isExpanded && (
                    <div className="px-4 py-4 space-y-3" style={{ background: "var(--surface-deep)", borderTop: "1px solid var(--surface-border)" }}>
                      <div className="text-xs"><span className="text-[10px] font-medium" style={{ color: "var(--text-muted)" }}>📋 摘要：</span><span style={{ color: "var(--text-secondary)" }}>{item.ai_summary}</span></div>
                      <div className="text-xs p-3 rounded-lg" style={{ background: "var(--surface-card)", border: "1px solid var(--surface-border)" }}>
                        <span className="text-[10px] font-medium" style={{ color: "var(--info)" }}>🤖 AI：</span>
                        <span style={{ color: "var(--text-secondary)" }}>{item.ai_comment}</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <div className="flex-1 text-[10px] p-2.5 rounded-lg" style={{ background: "rgba(0,196,140,0.05)", color: "var(--loss)" }}>{item.ai_fund_advice}</div>
                        <div className="text-[10px] p-2.5 rounded-lg" style={{ background: "rgba(212,168,67,0.05)", color: "var(--accent)" }}>{item.ai_risk_note}</div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
