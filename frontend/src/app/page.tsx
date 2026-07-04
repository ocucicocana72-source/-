/* 首页 — 暗色终端风格 */

"use client";
import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import TickerStrip from "./TickerStrip";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const FUND_TYPES = [
  { value: "股票型", label: "股票型" }, { value: "混合型", label: "混合型" },
  { value: "债券型", label: "债券型" }, { value: "指数型", label: "指数型" },
  { value: "QDII", label: "QDII" },
];

interface FundItem { code: string; name: string; nav: number | null; one_year_return: number | null; daily_return: number | null; }
interface NewsItem { title: string; url: string; source: string; time: string; sentiment: string; }
interface MoodData { score: number; label: string; positive_ratio: number; negative_ratio: number; total_news: number; }

export default function Home() {
  const [funds, setFunds] = useState<FundItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [fundType, setFundType] = useState("股票型");
  const [limit, setLimit] = useState(50);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [mood, setMood] = useState<MoodData | null>(null);
  const [compareList, setCompareList] = useState<{code: string; name: string}[]>([]);
  const [searchResults, setSearchResults] = useState<{code: string; name: string; type: string}[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [searchTimer, setSearchTimer] = useState<NodeJS.Timeout | null>(null);

  /* 实时搜索：输入变化时触发（300ms 防抖） */
  function handleSearchInput(value: string) {
    setQuery(value);
    if (searchTimer) clearTimeout(searchTimer);
    if (value.trim().length < 1) { setSearchResults([]); setShowDropdown(false); return; }
    const timer = setTimeout(async () => {
      try {
        const res = await fetch(`${API}/api/fund/search?q=${encodeURIComponent(value.trim())}&limit=15`);
        const data = await res.json();
        setSearchResults(data.results || []);
        setShowDropdown(true);
      } catch {}
    }, 300);
    setSearchTimer(timer);
  }

  function toggleCompare(code: string, name: string) {
    if (compareList.find(f => f.code === code)) setCompareList(compareList.filter(f => f.code !== code));
    else if (compareList.length < 5) setCompareList([...compareList, { code, name }]);
  }

  const fetchFunds = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const res = await fetch(`${API}/api/fund/list?type=${encodeURIComponent(fundType)}&limit=${limit}`);
      const data = await res.json(); setFunds(data.funds || []);
    } catch { setError("无法连接后端"); } finally { setLoading(false); }
  }, [fundType, limit]);

  const fetchNews = useCallback(async () => {
    try { const res = await fetch(`${API}/api/news/?limit=10`); const data = await res.json(); setNews(data.news || []); } catch {}
  }, []);

  const fetchMood = useCallback(async () => {
    try { const res = await fetch(`${API}/api/news/market-mood`); const data = await res.json(); setMood(data); } catch {}
  }, []);

  useEffect(() => { fetchFunds(); fetchNews(); fetchMood(); }, [fetchFunds, fetchNews, fetchMood]);
  useEffect(() => { const t = setInterval(() => { fetchNews(); fetchMood(); }, 30000); return () => clearInterval(t); }, [fetchNews, fetchMood]);

  async function handleSearch() {
    if (!query.trim()) { fetchFunds(); return; }
    setLoading(true);
    try { const res = await fetch(`${API}/api/fund/search?q=${encodeURIComponent(query)}`); const data = await res.json(); setFunds(data.results || []); }
    catch { setError("搜索失败"); } finally { setLoading(false); }
  }

  // 暗色输入框样式
  const inputCls = "px-3 py-2 rounded-lg text-sm outline-none transition-colors";
  const inputStyle = { background: "var(--surface-card)", color: "var(--text-primary)", border: "1px solid var(--surface-border)" };
  const focusStyle = { borderColor: "var(--accent)" };

  return (
    <div className="min-h-screen" style={{ background: "var(--surface-deep)", color: "var(--text-primary)" }}>
      {/* 行情滚动条 */}
      <TickerStrip />

      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* 页头 */}
        <header className="mb-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold" style={{ fontFamily: "var(--font-serif), serif", color: "var(--text-primary)" }}>
                基金智能分析助手
              </h1>
              <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
                支付宝基金深度分析 · 多源新闻 · AI 投资建议
              </p>
            </div>
            {mood && (
              <div className="flex items-center gap-4 px-4 py-2.5 rounded-lg" style={{ background: "var(--surface-card)", border: "1px solid var(--surface-border)" }}>
                <div className="text-center">
                  <div className="text-xl font-bold" style={{ fontFamily: "var(--font-geist-mono)", color: mood.score > 60 ? "var(--gain)" : mood.score < 40 ? "var(--loss)" : "var(--text-secondary)" }}>
                    {mood.score}
                  </div>
                  <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>市场情绪</div>
                </div>
                <div className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  <span style={{ color: "var(--gain)" }}>利好 {mood.positive_ratio}%</span>
                  {" / "}
                  <span style={{ color: "var(--loss)" }}>利空 {mood.negative_ratio}%</span>
                  <div className="text-[10px] mt-0.5" style={{ color: "var(--text-muted)" }}>{mood.label} · {mood.total_news}条新闻</div>
                </div>
              </div>
            )}
          </div>
          <div className="divider-gold" />
        </header>

        {/* 控制栏 */}
        <div className="mb-5 flex flex-wrap gap-2">
          <div className="relative flex-1 min-w-[180px]">
            <input type="text" placeholder="输入基金代码或名称实时搜索..." value={query}
              onChange={e => handleSearchInput(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter") { handleSearch(); setShowDropdown(false); } }}
              onFocus={() => { if (searchResults.length) setShowDropdown(true); }}
              onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
              className={inputCls + " w-full"} style={inputStyle} />
            {/* 实时搜索下拉 */}
            {showDropdown && searchResults.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 rounded-lg overflow-y-auto z-50 max-h-[400px]"
                style={{ background: "var(--surface-card)", border: "1px solid var(--surface-border)", boxShadow: "0 8px 32px rgba(0,0,0,0.5)" }}>
                {searchResults.map(f => (
                  <a key={f.code} href={`/fund/${f.code}`}
                    className="flex items-center gap-3 px-3 py-2.5 transition-colors block"
                    onMouseEnter={e => (e.currentTarget.style.background = "var(--surface-hover)")}
                    onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
                  >
                    <span className="text-xs font-medium" style={{ fontFamily: "var(--font-geist-mono)", color: "var(--accent)" }}>{f.code}</span>
                    <span className="text-xs flex-1 truncate" style={{ color: "var(--text-primary)" }}>{f.name}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: "var(--surface-deep)", color: "var(--text-muted)" }}>{f.type}</span>
                  </a>
                ))}
                <div className="px-3 py-2 text-[10px] text-center" style={{ color: "var(--text-muted)", borderTop: "1px solid var(--surface-border)" }}>
                  共 {searchResults.length} 个结果 · 回车搜索全部
                </div>
              </div>
            )}
          </div>
          <select value={fundType} onChange={e => setFundType(e.target.value)} className={inputCls} style={inputStyle}>
            {FUND_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
          <select value={limit} onChange={e => setLimit(Number(e.target.value))} className={inputCls} style={inputStyle}>
            <option value={20}>20条</option><option value={50}>50条</option><option value={100}>100条</option>
          </select>
          <button onClick={handleSearch} className="px-4 py-2 rounded-lg text-sm font-medium text-black" style={{ background: "var(--accent)" }}>
            搜索
          </button>
          <Link href="/news" className="px-3 py-2 rounded-lg text-sm" style={{ background: "var(--surface-card)", color: "var(--info)", border: "1px solid var(--surface-border)" }}>
            📰 新闻
          </Link>
          <Link href="/compare" className="px-3 py-2 rounded-lg text-sm" style={{ background: "var(--surface-card)", color: "var(--accent)", border: "1px solid var(--surface-border)" }}>
            📊 对比
          </Link>
          <Link href="/portfolio" className="px-3 py-2 rounded-lg text-sm" style={{ background: "var(--surface-card)", color: "var(--loss)", border: "1px solid var(--surface-border)" }}>
            💰 持仓
          </Link>
        </div>

        {error && <div className="mb-4 p-3 rounded-lg text-sm" style={{ background: "rgba(255,77,79,0.1)", color: "var(--gain)", border: "1px solid rgba(255,77,79,0.2)" }}>{error}</div>}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* 左侧：基金列表 */}
          <div className="lg:col-span-2">
            {loading ? (
              <div className="text-center py-12" style={{ color: "var(--text-muted)" }}>加载中...</div>
            ) : (
              <>
                <div className="text-xs mb-2" style={{ color: "var(--text-muted)" }}>共 {funds.length} 只 · {fundType}</div>
                <div className="rounded-lg overflow-hidden" style={{ background: "var(--surface-card)", border: "1px solid var(--surface-border)" }}>
                  <div className="max-h-[600px] overflow-y-auto">
                    <table className="w-full text-sm">
                      <thead style={{ background: "var(--surface-deep)" }}>
                        <tr className="sticky top-0" style={{ background: "var(--surface-deep)" }}>
                          <th className="px-3 py-2.5 text-left text-xs font-medium" style={{ color: "var(--text-muted)" }}>代码</th>
                          <th className="px-3 py-2.5 text-left text-xs font-medium" style={{ color: "var(--text-muted)" }}>名称</th>
                          <th className="px-3 py-2.5 text-right text-xs font-medium" style={{ color: "var(--text-muted)" }}>净值</th>
                          <th className="px-3 py-2.5 text-right text-xs font-medium" style={{ color: "var(--text-muted)" }}>日涨跌</th>
                          <th className="px-3 py-2.5 text-right text-xs font-medium" style={{ color: "var(--text-muted)" }}>近1年</th>
                          <th className="px-3 py-2.5 text-center text-xs font-medium" style={{ color: "var(--text-muted)" }}>操作</th>
                        </tr>
                      </thead>
                      <tbody>
                        {funds.map((fund, idx) => {
                          const inCompare = compareList.some(f => f.code === fund.code);
                          return (
                            <tr key={fund.code}
                              className="transition-colors"
                              style={{ borderTop: "1px solid var(--surface-border)", background: idx % 2 === 0 ? "transparent" : "rgba(255,255,255,0.02)" }}
                              onMouseEnter={e => (e.currentTarget.style.background = "var(--surface-hover)")}
                              onMouseLeave={e => (e.currentTarget.style.background = idx % 2 === 0 ? "transparent" : "rgba(255,255,255,0.02)")}
                            >
                              <td className="px-3 py-2 text-xs" style={{ fontFamily: "var(--font-geist-mono)", color: "var(--text-muted)" }}>{fund.code}</td>
                              <td className="px-3 py-2 font-medium truncate max-w-[200px]" style={{ color: "var(--text-primary)" }}>{fund.name}</td>
                              <td className="px-3 py-2 text-right tabular" style={{ fontFamily: "var(--font-geist-mono)", color: "var(--text-primary)" }}>{fund.nav?.toFixed(4) ?? "-"}</td>
                              <td className="px-3 py-2 text-right font-medium tabular" style={{ fontFamily: "var(--font-geist-mono)", color: (fund.daily_return ?? 0) >= 0 ? "var(--gain)" : "var(--loss)" }}>
                                {fund.daily_return != null ? `${fund.daily_return >= 0 ? "+" : ""}${fund.daily_return.toFixed(2)}%` : "-"}
                              </td>
                              <td className="px-3 py-2 text-right font-medium tabular" style={{ fontFamily: "var(--font-geist-mono)", color: (fund.one_year_return ?? 0) >= 0 ? "var(--gain)" : "var(--loss)" }}>
                                {fund.one_year_return != null ? `${fund.one_year_return >= 0 ? "+" : ""}${fund.one_year_return.toFixed(2)}%` : "-"}
                              </td>
                              <td className="px-3 py-2 text-center whitespace-nowrap">
                                <a href={`/fund/${fund.code}`} className="text-xs font-medium" style={{ color: "var(--info)" }}>分析</a>
                                <button onClick={() => toggleCompare(fund.code, fund.name)}
                                  className="ml-1.5 text-xs px-1.5 py-0.5 rounded transition-colors"
                                  style={inCompare ? { background: "var(--accent)", color: "#000" } : { color: "var(--text-muted)" }}>
                                  {inCompare ? "✓" : "对比"}
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* 右侧：新闻面板 */}
          <div className="lg:col-span-1">
            <div className="rounded-lg p-4" style={{ background: "var(--surface-card)", border: "1px solid var(--surface-border)" }}>
              <h2 className="font-bold text-sm mb-3 flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
                📰 财经新闻 <span className="text-[10px] font-normal" style={{ color: "var(--text-muted)" }}>多源聚合</span>
              </h2>
              {news.length === 0 ? (
                <div className="text-sm py-4 text-center" style={{ color: "var(--text-muted)" }}>加载中...</div>
              ) : (
                <div className="space-y-2.5 max-h-[500px] overflow-y-auto">
                  {news.map((item, i) => (
                    <a key={i} href={item.url} target="_blank" rel="noopener noreferrer"
                      className="block p-2.5 rounded-lg transition-colors group"
                      style={{ background: "var(--surface-deep)" }}
                      onMouseEnter={e => (e.currentTarget.style.background = "var(--surface-hover)")}
                      onMouseLeave={e => (e.currentTarget.style.background = "var(--surface-deep)")}
                    >
                      <div className="text-xs leading-relaxed line-clamp-2" style={{ color: "var(--text-primary)" }}>{item.title}</div>
                      <div className="flex items-center gap-2 mt-1.5">
                        <span className="text-[10px] px-1.5 py-0.5 rounded"
                          style={item.sentiment === "利好" ? { background: "rgba(255,77,79,0.1)", color: "var(--gain)" } :
                            item.sentiment === "利空" ? { background: "rgba(0,196,140,0.1)", color: "var(--loss)" } :
                            { background: "var(--surface-card)", color: "var(--text-muted)" }}>
                          {item.sentiment === "利好" ? "🟢" : item.sentiment === "利空" ? "🔴" : "⚪"} {item.sentiment}
                        </span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: "var(--surface-card)", color: "var(--text-muted)" }}>{item.source}</span>
                        <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>{item.time}</span>
                      </div>
                    </a>
                  ))}
                </div>
              )}
              <a href="/news" className="block text-center text-xs mt-3 pt-3" style={{ color: "var(--info)", borderTop: "1px solid var(--surface-border)" }}>
                查看更多新闻 →
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* 浮动对比栏 */}
      {compareList.length > 0 && (
        <div className="fixed bottom-0 left-0 right-0 z-50 px-6 py-3"
          style={{ background: "rgba(26,29,39,0.95)", borderTop: "1px solid var(--surface-border)", backdropFilter: "blur(12px)" }}>
          <div className="max-w-6xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>📊 已选 {compareList.length}/5：</span>
              {compareList.map(f => (
                <span key={f.code} className="px-2.5 py-1 rounded-full text-xs flex items-center gap-1"
                  style={{ background: "rgba(212,168,67,0.15)", color: "var(--accent)" }}>
                  {f.code} {f.name.slice(0, 4)}
                  <button onClick={() => toggleCompare(f.code, f.name)} style={{ color: "var(--accent-dim)" }}>×</button>
                </span>
              ))}
            </div>
            <div className="flex items-center gap-3">
              <button onClick={() => setCompareList([])} className="text-xs" style={{ color: "var(--text-muted)" }}>清空</button>
              <Link href={`/compare?codes=${compareList.map(f => f.code).join(",")}`}
                className="px-4 py-2 rounded-lg text-xs font-medium text-black"
                style={{ background: compareList.length >= 2 ? "var(--accent)" : "var(--surface-border)", cursor: compareList.length >= 2 ? "pointer" : "not-allowed" }}>
                开始对比{compareList.length < 2 ? "（至少2只）" : ""}
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
