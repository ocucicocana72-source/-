/* 基金对比页 — 暗色终端风格 */
"use client";
import { useState, useMemo, useEffect } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FundData {
  code: string; name: string; nav: number | null; manager: string;
  metrics: { annualized_return: number; max_drawdown: number; sharpe_ratio: number; volatility: number; calmar_ratio: number; };
  score: { total: number; return_score: number; risk_score: number; sharpe_score: number; recommendation: string; };
  top3_holdings: { stock_name: string; percentage: number; }[];
}
interface AiConclusion { winner: { code: string; name: string; score: number; }; reasons: string[]; conclusion: string; investor_type: string; summary_text: string; }
interface CompareResult { funds: FundData[]; summary: { best_return: { code: string; name: string; value: number; }; best_sharpe: { code: string; name: string; value: number; }; lowest_risk: { code: string; name: string; value: number; }; best_score: { code: string; name: string; value: number; }; ai_conclusion: AiConclusion; }; }

const COLORS = ["#FF4D4F", "#5B8DEF", "#00C48C", "#A78BFA", "#D4A843"];
const cardStyle = { background: "var(--surface-card)", border: "1px solid var(--surface-border)" };
const inputCls = "px-4 py-2 rounded-lg text-sm outline-none transition-colors";
const inputStyle = { background: "var(--surface-card)", color: "var(--text-primary)", border: "1px solid var(--surface-border)" };

export default function ComparePage() {
  const searchParams = useSearchParams();
  const [input, setInput] = useState("");
  const [codes, setCodes] = useState<string[]>([]);
  const [data, setData] = useState<CompareResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { const c = searchParams.get("codes"); if (c) setCodes(c.split(",").filter(x => x.trim())); }, [searchParams]);
  useEffect(() => { if (codes.length >= 2 && !data && !loading) doCompare(); }, [codes]);

  function addCode() {
    const c = input.trim(); if (!c || codes.includes(c)) { setInput(""); return; }
    if (codes.length >= 5) { setError("最多5只"); return; }
    setCodes([...codes, c]); setInput("");
  }

  async function doCompare() {
    if (codes.length < 2) { setError("至少2只"); return; }
    setLoading(true); setError(null);
    try {
      const res = await fetch(`${API}/api/compare/funds`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ codes, period: "1y" }) });
      const d = await res.json(); if (d.error) { setError(d.error); return; } setData(d);
    } catch { setError("请求失败"); } finally { setLoading(false); }
  }

  const radarOption = useMemo(() => {
    if (!data) return {};
    return {
      tooltip: {}, legend: { data: data.funds.map(f => f.name), bottom: 0, textStyle: { color: "#8B8FA3", fontSize: 10 } },
      radar: { indicator: [{ name: "年化收益", max: 60 }, { name: "风控", max: 100 }, { name: "夏普", max: 100 }, { name: "评分", max: 100 }], shape: "circle", axisName: { color: "#8B8FA3", fontSize: 10 }, splitLine: { lineStyle: { color: "#2A2E3D" } }, splitArea: { areaStyle: { color: ["rgba(26,29,39,0.8)", "rgba(15,17,23,0.8)"] } }, axisLine: { lineStyle: { color: "#2A2E3D" } } },
      series: [{ type: "radar", data: data.funds.map((f, i) => ({ name: f.name, value: [Math.min(f.metrics.annualized_return, 60), Math.max(100 - Math.abs(f.metrics.max_drawdown) * 2, 0), Math.min(Math.max(f.metrics.sharpe_ratio / 3 * 100, 0), 100), f.score.total], areaStyle: { opacity: 0.1 }, lineStyle: { color: COLORS[i] }, itemStyle: { color: COLORS[i] } })) }],
    };
  }, [data]);

  const fmt = (v: number | null, d = 2) => v != null ? v.toFixed(d) : "-";

  return (
    <div className="min-h-screen" style={{ background: "var(--surface-deep)", color: "var(--text-primary)" }}>
      <div className="max-w-6xl mx-auto px-4 py-6">
        <header className="mb-6">
          <Link href="/" className="text-xs" style={{ color: "var(--info)" }}>← 返回首页</Link>
          <h1 className="text-xl font-bold mt-2" style={{ fontFamily: "var(--font-serif), serif" }}>📊 基金对比</h1>
          <p className="text-[10px] mt-1" style={{ color: "var(--text-muted)" }}>输入基金代码，横向对比（2~5只）</p>
          <div className="divider-gold" />
        </header>

        {/* 输入区 */}
        <div className="rounded-lg p-5 mb-6" style={cardStyle}>
          <div className="flex gap-2 mb-3">
            <input type="text" value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && addCode()}
              placeholder="输入基金代码，如 006265" className={inputCls + " flex-1"} style={inputStyle} />
            <button onClick={addCode} className="px-4 py-2 rounded-lg text-sm" style={{ background: "var(--surface-deep)", color: "var(--text-secondary)", border: "1px solid var(--surface-border)" }}>添加</button>
            <button onClick={doCompare} disabled={codes.length < 2} className="px-5 py-2 rounded-lg text-sm font-medium text-black"
              style={{ background: codes.length >= 2 ? "var(--accent)" : "var(--surface-border)" }}>开始对比</button>
          </div>
          {codes.length > 0 && (
            <div className="flex gap-2 flex-wrap">
              {codes.map((c, i) => (
                <span key={c} className="px-3 py-1 rounded-full text-xs flex items-center gap-1"
                  style={{ background: `${COLORS[i]}20`, color: COLORS[i], border: `1px solid ${COLORS[i]}40` }}>
                  {c} <button onClick={() => setCodes(codes.filter(x => x !== c))} style={{ opacity: 0.7 }}>×</button>
                </span>
              ))}
            </div>
          )}
          {error && <div className="mt-2 text-xs" style={{ color: "var(--gain)" }}>{error}</div>}
        </div>

        {loading && <div className="text-center py-8" style={{ color: "var(--text-muted)" }}>对比分析中...</div>}

        {data && (
          <div className="space-y-5">
            {/* 对比结论 */}
            <div className="rounded-lg p-5" style={cardStyle}>
              <div className="text-[10px] mb-3" style={{ color: "var(--text-muted)" }}>🏆 对比结论</div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: "最高收益", name: data.summary.best_return.name, value: `+${fmt(data.summary.best_return.value)}%`, color: "var(--gain)" },
                  { label: "最高夏普", name: data.summary.best_sharpe.name, value: fmt(data.summary.best_sharpe.value, 2), color: "var(--info)" },
                  { label: "最低回撤", name: data.summary.lowest_risk.name, value: `${fmt(data.summary.lowest_risk.value)}%`, color: "var(--accent)" },
                  { label: "最高评分", name: data.summary.best_score.name, value: fmt(data.summary.best_score.value, 1), color: "var(--gain)" },
                ].map(m => (
                  <div key={m.label}>
                    <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>{m.label}</div>
                    <div className="font-bold text-xs truncate" style={{ color: "var(--text-primary)" }}>{m.name}</div>
                    <div className="text-sm font-bold" style={{ fontFamily: "var(--font-geist-mono)", color: m.color }}>{m.value}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* AI 总结 */}
            {data.summary.ai_conclusion && (
              <div className="rounded-lg p-5" style={{ ...cardStyle, borderLeft: "3px solid var(--accent)" }}>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-base">🤖</span>
                  <span className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>AI 对比分析报告</span>
                </div>
                <div className="rounded-lg p-3 mb-4" style={{ background: "var(--surface-deep)", border: "1px solid var(--surface-border)" }}>
                  <div className="text-xs" style={{ color: "var(--text-secondary)" }}>{data.summary.ai_conclusion.summary_text}</div>
                </div>
                <div className="space-y-2 mb-4">
                  <div className="text-[10px] font-medium" style={{ color: "var(--text-muted)" }}>📊 分析依据：</div>
                  {data.summary.ai_conclusion.reasons.map((r, i) => (
                    <div key={i} className="text-xs pl-3" style={{ color: "var(--text-secondary)", borderLeft: "2px solid var(--surface-border)" }}>• {r}</div>
                  ))}
                </div>
                <div className="flex flex-wrap gap-3">
                  <div className="flex-1 rounded-lg p-3" style={{ background: "rgba(0,196,140,0.05)", border: "1px solid rgba(0,196,140,0.2)" }}>
                    <div className="text-[10px] font-medium mb-1" style={{ color: "var(--loss)" }}>✅ 建议</div>
                    <div className="text-xs" style={{ color: "var(--text-secondary)" }}>{data.summary.ai_conclusion.conclusion}</div>
                  </div>
                  <div className="rounded-lg p-3" style={{ background: "rgba(167,139,250,0.05)", border: "1px solid rgba(167,139,250,0.2)" }}>
                    <div className="text-[10px] font-medium mb-1" style={{ color: "#A78BFA" }}>👤 适合人群</div>
                    <div className="text-xs" style={{ color: "var(--text-secondary)" }}>{data.summary.ai_conclusion.investor_type}</div>
                  </div>
                </div>
                <div className="mt-3 text-[10px] text-center" style={{ color: "var(--text-muted)" }}>AI 仅供参考</div>
              </div>
            )}

            {/* 雷达图 */}
            <div className="rounded-lg p-5" style={cardStyle}>
              <div className="text-[10px] mb-3" style={{ color: "var(--text-muted)" }}>雷达图对比</div>
              <ReactECharts option={radarOption} style={{ height: 320 }} />
            </div>

            {/* 指标表格 */}
            <div className="rounded-lg overflow-hidden" style={cardStyle}>
              <div className="text-[10px] p-5 pb-0" style={{ color: "var(--text-muted)" }}>详细指标</div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs mt-3">
                  <thead>
                    <tr style={{ background: "var(--surface-deep)" }}>
                      <th className="px-4 py-2 text-left" style={{ color: "var(--text-muted)" }}>指标</th>
                      {data.funds.map((f, i) => <th key={f.code} className="px-4 py-2 text-right" style={{ color: COLORS[i] }}>{f.name.slice(0, 6)}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { label: "代码", render: (f: FundData) => <span style={{ fontFamily: "var(--font-geist-mono)", color: "var(--text-muted)" }}>{f.code}</span> },
                      { label: "经理", render: (f: FundData) => f.manager },
                      { label: "评分", render: (f: FundData) => <b style={{ fontFamily: "var(--font-geist-mono)", color: "var(--accent)" }}>{f.score.total}</b> },
                      { label: "建议", render: (f: FundData) => <span className="px-2 py-0.5 rounded-full text-[10px]" style={{ background: "var(--accent)", color: "#000" }}>{f.score.recommendation}</span> },
                      { label: "年化收益", render: (f: FundData) => <span style={{ fontFamily: "var(--font-geist-mono)", color: f.metrics.annualized_return >= 0 ? "var(--gain)" : "var(--loss)" }}>{fmt(f.metrics.annualized_return)}%</span> },
                      { label: "最大回撤", render: (f: FundData) => <span style={{ fontFamily: "var(--font-geist-mono)", color: "var(--gain)" }}>{fmt(f.metrics.max_drawdown)}%</span> },
                      { label: "夏普", render: (f: FundData) => <span style={{ fontFamily: "var(--font-geist-mono)" }}>{fmt(f.metrics.sharpe_ratio, 4)}</span> },
                      { label: "波动率", render: (f: FundData) => <span style={{ fontFamily: "var(--font-geist-mono)" }}>{fmt(f.metrics.volatility)}%</span> },
                      { label: "前3持仓", render: (f: FundData) => f.top3_holdings.map(h => h.stock_name).join("、") },
                    ].map(row => (
                      <tr key={row.label} style={{ borderTop: "1px solid var(--surface-border)" }}>
                        <td className="px-4 py-2" style={{ color: "var(--text-muted)" }}>{row.label}</td>
                        {data.funds.map(f => <td key={f.code} className="px-4 py-2 text-right">{row.render(f)}</td>)}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
