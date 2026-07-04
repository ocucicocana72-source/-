/* 全历史净值走势 — 暗色终端风格 */
"use client";
import { useState, useEffect, useMemo } from "react";
import dynamic from "next/dynamic";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
interface NavPoint { date: string; nav: number; daily_return: number; }

const cardStyle = { background: "var(--surface-card)", border: "1px solid var(--surface-border)" };

export default function FullHistoryChart({ code }: { code: string }) {
  const [data, setData] = useState<NavPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/fund/${code}/nav?period=all`)
      .then(r => r.json()).then(d => setData(d.data || []))
      .catch(() => {}).finally(() => setLoading(false));
  }, [code]);

  const option = useMemo(() => {
    if (data.length < 2) return {};
    const dates = data.map(d => d.date); const navs = data.map(d => d.nav); const returns = data.map(d => d.daily_return);
    const isUp = navs[navs.length - 1] >= navs[0];
    return {
      tooltip: { trigger: "axis", backgroundColor: "#1A1D27", borderColor: "#2A2E3D", textStyle: { color: "#E8EAF0", fontSize: 12 },
        formatter: (params: { data: number; dataIndex: number }[]) => { const p = params[0]; const i = p.dataIndex; const ret = returns[i]; return `<div style="font-weight:600;margin-bottom:4px">${dates[i]}</div><div>净值：<b>${navs[i].toFixed(4)}</b></div><div>日涨跌：<span style="color:${ret >= 0 ? "#FF4D4F" : "#00C48C"}">${ret >= 0 ? "+" : ""}${ret.toFixed(2)}%</span></div>`; } },
      grid: { top: 20, right: 20, bottom: 30, left: 50 },
      xAxis: { type: "category", data: dates, axisLabel: { formatter: (v: string) => v.slice(0, 7), fontSize: 10, color: "#5A5E72" }, axisLine: { lineStyle: { color: "#2A2E3D" } }, axisTick: { show: false } },
      yAxis: { type: "value", scale: true, axisLabel: { formatter: (v: number) => v.toFixed(2), fontSize: 10, color: "#5A5E72" }, splitLine: { lineStyle: { color: "#1A1D27" } } },
      series: [{ type: "line", data: navs, smooth: 0.3, symbol: "none", lineStyle: { color: isUp ? "#FF4D4F" : "#00C48C", width: 1.5 },
        areaStyle: { color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: isUp ? "rgba(255,77,79,0.12)" : "rgba(0,196,140,0.12)" }, { offset: 1, color: "rgba(15,17,23,0)" }] } },
        markPoint: { data: [{ type: "max", symbolSize: 40, label: { formatter: "{c}", fontSize: 10 } }, { type: "min", symbolSize: 40, label: { formatter: "{c}", fontSize: 10 } }], itemStyle: { color: isUp ? "#FF4D4F" : "#00C48C" } } }],
      dataZoom: [{ type: "inside", start: 0, end: 100 }],
    };
  }, [data]);

  if (loading) return <div className="rounded-lg p-5 text-center text-sm" style={{ ...cardStyle, color: "var(--text-muted)" }}>加载历史数据...</div>;
  if (data.length < 2) return <div className="rounded-lg p-5 text-center text-sm" style={{ ...cardStyle, color: "var(--text-muted)" }}>数据不足</div>;

  const navs = data.map(d => d.nav);
  const totalReturn = ((navs[navs.length - 1] / navs[0]) - 1) * 100;
  const isUp = totalReturn >= 0;

  return (
    <div className="rounded-lg p-5" style={cardStyle}>
      <div className="flex items-center justify-between mb-3">
        <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>成立以来净值走势</div>
        <div className="flex items-center gap-4 text-[10px]">
          <span style={{ color: "var(--text-muted)" }}>{data[0].date} → {data[data.length - 1].date}</span>
          <span style={{ fontFamily: "var(--font-geist-mono)", color: isUp ? "var(--gain)" : "var(--loss)" }}>{isUp ? "+" : ""}{totalReturn.toFixed(2)}%</span>
        </div>
      </div>
      <ReactECharts option={option} style={{ height: 260 }} />
      <div className="text-[10px] text-center mt-1" style={{ color: "var(--text-muted)" }}>鼠标悬停查看 · 滚轮缩放</div>
    </div>
  );
}
