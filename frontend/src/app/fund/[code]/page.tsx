/* 基金详情页 — 暗色终端风格 */

"use client";
import { useState, useEffect, use, useMemo } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import FullHistoryChart from "./FullHistoryChart";
import AiReviewCard from "./AiReviewCard";
import CommentsCard from "./CommentsCard";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FundInfo { code: string; name: string; nav: number | null; one_year_return: number | null; }
interface RiskMetrics { annualized_return: number; max_drawdown: number; sharpe_ratio: number; volatility: number; calmar_ratio: number; downside_risk: number; }
interface ScoreData { score: number; recommendation: string; breakdown: { return_score: number; risk_score: number; sharpe_score: number; }; }
interface Holding { stock_code: string; stock_name: string; percentage: number; }
interface NavPoint { date: string; nav: number; daily_return: number; }
interface ManagerData { manager_name: string; tenure: string; return_since: string; company: string; }
interface DriftData { drift_score: number; is_drifting: boolean; overlap: number; description: string; old_quarter: string; new_quarter: string; }

/* 暗色卡片样式 */
const cardStyle = { background: "var(--surface-card)", border: "1px solid var(--surface-border)" };
const labelStyle = { color: "var(--text-muted)" };
const monoStyle = { fontFamily: "var(--font-geist-mono)" };

export default function FundDetail({ params }: { params: Promise<{ code: string }> }) {
  const { code } = use(params);
  const [info, setInfo] = useState<FundInfo | null>(null);
  const [risk, setRisk] = useState<RiskMetrics | null>(null);
  const [score, setScore] = useState<ScoreData | null>(null);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [navData, setNavData] = useState<NavPoint[]>([]);
  const [manager, setManager] = useState<ManagerData | null>(null);
  const [drift, setDrift] = useState<DriftData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAll() {
      try {
        const [infoRes, riskRes, scoreRes, holdRes, navRes, mgrRes, driftRes] = await Promise.all([
          fetch(`${API}/api/fund/${code}`), fetch(`${API}/api/analysis/${code}/risk?period=1y`),
          fetch(`${API}/api/analysis/${code}/score`), fetch(`${API}/api/fund/${code}/holdings`),
          fetch(`${API}/api/fund/${code}/nav?period=1y`), fetch(`${API}/api/analysis/${code}/manager`),
          fetch(`${API}/api/analysis/${code}/style-drift`),
        ]);
        const [infoD, riskD, scoreD, holdD, navD, mgrD, driftD] = await Promise.all([
          infoRes.json(), riskRes.json(), scoreRes.json(), holdRes.json(), navRes.json(), mgrRes.json(), driftRes.json(),
        ]);
        setInfo(infoD); setRisk(riskD.metrics || null); setScore(scoreD.error ? null : scoreD);
        setHoldings(holdD.holdings || []); setNavData(navD.data || []);
        setManager(mgrD.manager_name ? mgrD : null); setDrift(driftD.error ? null : driftD);
      } catch { setError("数据加载失败"); } finally { setLoading(false); }
    }
    loadAll();
  }, [code]);

  function scoreColor(s: number) { return s >= 80 ? "var(--gain)" : s >= 60 ? "#E6A817" : s >= 40 ? "var(--text-secondary)" : "var(--text-muted)"; }
  function fmt(v: number | null, d = 2) { return v != null ? v.toFixed(d) : "-"; }

  /* 近1年走势 ECharts */
  function NavChart({ data }: { data: NavPoint[] }) {
    const option = useMemo(() => {
      if (data.length < 2) return {};
      const dates = data.map(d => d.date); const navs = data.map(d => d.nav); const returns = data.map(d => d.daily_return);
      const isUp = navs[navs.length - 1] >= navs[0];
      return {
        tooltip: { trigger: "axis", backgroundColor: "#1A1D27", borderColor: "#2A2E3D", textStyle: { color: "#E8EAF0", fontSize: 12 },
          formatter: (params: { data: number; dataIndex: number }[]) => { const p = params[0]; const i = p.dataIndex; const ret = returns[i]; return `<div style="font-weight:600;margin-bottom:4px">${dates[i]}</div><div>净值：<b>${navs[i].toFixed(4)}</b></div><div>日涨跌：<span style="color:${ret >= 0 ? "#FF4D4F" : "#00C48C"};font-weight:600">${ret >= 0 ? "+" : ""}${ret.toFixed(2)}%</span></div>`; } },
        grid: { top: 15, right: 15, bottom: 25, left: 45 },
        xAxis: { type: "category", data: dates, axisLabel: { formatter: (v: string) => v.slice(5), fontSize: 10, color: "#5A5E72" }, axisLine: { lineStyle: { color: "#2A2E3D" } }, axisTick: { show: false } },
        yAxis: { type: "value", scale: true, axisLabel: { formatter: (v: number) => v.toFixed(2), fontSize: 10, color: "#5A5E72" }, splitLine: { lineStyle: { color: "#1A1D27" } } },
        series: [{ type: "line", data: navs, smooth: 0.3, symbol: "none", lineStyle: { color: isUp ? "#FF4D4F" : "#00C48C", width: 2 },
          areaStyle: { color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: isUp ? "rgba(255,77,79,0.15)" : "rgba(0,196,140,0.15)" }, { offset: 1, color: "rgba(15,17,23,0)" }] } },
          markPoint: { data: [{ type: "max", name: "最高", symbolSize: 36, label: { formatter: "{c}", fontSize: 10 } }, { type: "min", name: "最低", symbolSize: 36, label: { formatter: "{c}", fontSize: 10 } }], itemStyle: { color: isUp ? "#FF4D4F" : "#00C48C" } } }],
      };
    }, [data]);
    if (data.length < 2) return <div className="text-sm py-8 text-center" style={{ color: "var(--text-muted)" }}>数据不足</div>;
    return <ReactECharts option={option} style={{ height: 200 }} />;
  }

  if (loading) return <div className="min-h-screen flex items-center justify-center" style={{ color: "var(--text-muted)" }}>加载中...</div>;
  if (error) return <div className="min-h-screen flex items-center justify-center" style={{ color: "var(--gain)" }}>{error}</div>;

  return (
    <div className="min-h-screen" style={{ background: "var(--surface-deep)", color: "var(--text-primary)" }}>
      <div className="max-w-5xl mx-auto px-4 py-6">
        {/* 页头 */}
        <header className="mb-6">
          <div className="flex items-center gap-4">
            <Link href="/" className="text-xs" style={{ color: "var(--info)" }}>← 返回首页</Link>
            <Link href={`/compare?add=${code}`} className="text-xs px-2.5 py-1 rounded" style={{ background: "rgba(212,168,67,0.15)", color: "var(--accent)" }}>📊 加入对比</Link>
          </div>
          <div className="flex items-end gap-4 mt-3">
            <h1 className="text-xl font-bold" style={{ fontFamily: "var(--font-serif), serif", color: "var(--text-primary)" }}>{info?.name || code}</h1>
            <span className="text-xs pb-0.5" style={{ fontFamily: "var(--font-geist-mono)", color: "var(--text-muted)" }}>{code}</span>
          </div>
          <div className="flex items-center gap-6 mt-2 text-xs" style={{ color: "var(--text-secondary)" }}>
            <span>净值 <b style={{ color: "var(--text-primary)", fontFamily: "var(--font-geist-mono)" }}>{fmt(info?.nav ?? null, 4)}</b></span>
            <span>近1年 <b style={{ fontFamily: "var(--font-geist-mono)", color: (info?.one_year_return ?? 0) >= 0 ? "var(--gain)" : "var(--loss)" }}>
              {info?.one_year_return != null ? `${info.one_year_return >= 0 ? "+" : ""}${fmt(info.one_year_return)}%` : "-"}
            </b></span>
          </div>
          <div className="divider-gold" />
        </header>

        <div className="space-y-5">
          {/* 评分 + 风险 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="rounded-lg p-5 text-center" style={cardStyle}>
              <div className="text-[10px] mb-2" style={labelStyle}>综合评分</div>
              {score ? (
                <>
                  <div className="text-4xl font-bold" style={{ fontFamily: "var(--font-geist-mono)", color: scoreColor(score.score) }}>{score.score}</div>
                  <div className="inline-block mt-2 px-3 py-1 rounded-full text-xs text-black font-medium" style={{ background: scoreColor(score.score) }}>{score.recommendation}</div>
                  <div className="mt-2 text-[10px]" style={labelStyle}>收益 {score.breakdown.return_score} · 风控 {score.breakdown.risk_score} · 夏普 {score.breakdown.sharpe_score}</div>
                </>
              ) : <div style={{ color: "var(--text-muted)" }}>数据不足</div>}
            </div>
            <div className="md:col-span-2 rounded-lg p-5" style={cardStyle}>
              <div className="text-[10px] mb-3" style={labelStyle}>风险指标（近1年）</div>
              {risk ? (
                <div className="grid grid-cols-3 gap-4 text-center">
                  {[
                    { label: "年化收益", value: `${fmt(risk.annualized_return)}%`, color: risk.annualized_return >= 0 ? "var(--gain)" : "var(--loss)" },
                    { label: "最大回撤", value: `${fmt(risk.max_drawdown)}%`, color: "var(--gain)" },
                    { label: "夏普比率", value: fmt(risk.sharpe_ratio, 4), color: "var(--text-primary)" },
                    { label: "波动率", value: `${fmt(risk.volatility)}%`, color: "var(--text-primary)" },
                    { label: "Calmar", value: fmt(risk.calmar_ratio, 4), color: "var(--text-primary)" },
                    { label: "下行风险", value: `${fmt(risk.downside_risk)}%`, color: "var(--accent)" },
                  ].map(m => (
                    <div key={m.label}>
                      <div className="text-sm font-bold" style={{ fontFamily: "var(--font-geist-mono)", color: m.color }}>{m.value}</div>
                      <div className="text-[10px]" style={labelStyle}>{m.label}</div>
                    </div>
                  ))}
                </div>
              ) : <div className="text-center" style={{ color: "var(--text-muted)" }}>加载中...</div>}
            </div>
          </div>

          {/* 近1年走势 */}
          <div className="rounded-lg p-5" style={cardStyle}>
            <div className="text-[10px] mb-3" style={labelStyle}>净值走势（近1年）</div>
            <NavChart data={navData} />
            <div className="flex justify-between text-[10px] mt-2 px-2" style={labelStyle}>
              <span>最高 <b style={{ color: "var(--text-primary)", fontFamily: "var(--font-geist-mono)" }}>{fmt(Math.max(...navData.map(d => d.nav)), 4)}</b></span>
              <span>最低 <b style={{ color: "var(--text-primary)", fontFamily: "var(--font-geist-mono)" }}>{fmt(Math.min(...navData.map(d => d.nav)), 4)}</b></span>
              <span>共 <b style={{ color: "var(--text-primary)" }}>{navData.length}</b> 个交易日</span>
            </div>
          </div>

          {/* 风格漂移 */}
          {drift && (
            <div className="rounded-lg p-5" style={cardStyle}>
              <div className="flex items-center justify-between mb-3">
                <div className="text-[10px]" style={labelStyle}>风格漂移检测</div>
                <span className="text-[10px]" style={labelStyle}>{drift.old_quarter?.replace("股票投资明细", "")} → {drift.new_quarter?.replace("股票投资明细", "")}</span>
              </div>
              <div className="flex items-center gap-6">
                <div className="text-center">
                  <div className="text-2xl font-bold" style={{ fontFamily: "var(--font-geist-mono)", color: drift.drift_score > 60 ? "var(--gain)" : drift.drift_score > 30 ? "var(--accent)" : "var(--loss)" }}>{drift.drift_score}</div>
                  <div className="text-[10px]" style={labelStyle}>漂移分数</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold" style={{ fontFamily: "var(--font-geist-mono)", color: "var(--text-primary)" }}>{drift.overlap}%</div>
                  <div className="text-[10px]" style={labelStyle}>持仓重合</div>
                </div>
                <div className="flex-1 text-xs" style={{ color: "var(--text-secondary)" }}>
                  <div className="inline-block px-2 py-0.5 rounded text-[10px] mb-1"
                    style={drift.is_drifting ? { background: "rgba(255,77,79,0.1)", color: "var(--gain)" } : { background: "rgba(0,196,140,0.1)", color: "var(--loss)" }}>
                    {drift.is_drifting ? "⚠️ 风格漂移" : "✅ 风格稳定"}
                  </div>
                  <div>{drift.description}</div>
                </div>
              </div>
            </div>
          )}

          {/* 全历史走势 */}
          <FullHistoryChart code={code} />

          {/* AI 分析 */}
          <AiReviewCard code={code} />

          {/* 基民评论 */}
          <CommentsCard code={code} />

          {/* 持仓 + 经理 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-lg p-5" style={cardStyle}>
              <div className="text-[10px] mb-3" style={labelStyle}>前十大持仓</div>
              {holdings.length > 0 ? (
                <div className="space-y-2">
                  {holdings.slice(0, 10).map((h, i) => (
                    <div key={i} className="flex items-center gap-3 text-xs">
                      <span className="w-5 text-right" style={{ color: "var(--text-muted)" }}>{i + 1}</span>
                      <span className="flex-1 truncate" style={{ color: "var(--text-primary)" }}>{h.stock_name}</span>
                      <span style={{ fontFamily: "var(--font-geist-mono)", color: "var(--text-muted)" }}>{h.stock_code}</span>
                      <span className="w-14 text-right font-medium" style={{ fontFamily: "var(--font-geist-mono)", color: "var(--text-primary)" }}>{h.percentage.toFixed(2)}%</span>
                    </div>
                  ))}
                </div>
              ) : <div className="text-center" style={{ color: "var(--text-muted)" }}>暂无数据</div>}
            </div>
            <div className="rounded-lg p-5" style={cardStyle}>
              <div className="text-[10px] mb-3" style={labelStyle}>基金经理</div>
              {manager ? (
                <div className="space-y-3">
                  <div className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>{manager.manager_name}</div>
                  <div className="space-y-1.5 text-xs" style={{ color: "var(--text-secondary)" }}>
                    <div>🏢 {manager.company || "未知"}</div>
                    <div>📅 任职时间：{manager.tenure || "未知"}</div>
                    <div>📈 任职回报：{manager.return_since || "未知"}</div>
                  </div>
                </div>
              ) : <div className="text-center" style={{ color: "var(--text-muted)" }}>暂无信息</div>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
