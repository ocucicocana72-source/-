/* AI 分析卡片 — 暗色终端风格 */
"use client";
import { useState, useEffect } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
interface AiReview {
  emoji: string; verdict: string; action: string; investor_type: string; score: number;
  summary: { total_return: number; annualized_return: number; max_drawdown: number; sharpe_ratio: number; volatility: number; calmar_ratio: number; years: number; };
  strengths: string[]; risks: string[]; tags: string[]; manager: string; manager_tenure: string;
}

export default function AiReviewCard({ code }: { code: string }) {
  const [review, setReview] = useState<AiReview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/analysis/${code}/ai-review`)
      .then(r => r.json()).then(d => { if (!d.error) setReview(d); })
      .catch(() => {}).finally(() => setLoading(false));
  }, [code]);

  if (loading) return <div className="rounded-lg p-5 text-center text-sm" style={{ background: "var(--surface-card)", border: "1px solid var(--surface-border)", color: "var(--text-muted)" }}>AI 分析中...</div>;
  if (!review) return null;

  const fmt = (v: number, d = 2) => v.toFixed(d);

  return (
    <div className="rounded-lg overflow-hidden" style={{ background: "var(--surface-card)", border: "1px solid var(--surface-border)" }}>
      {/* 顶部金色线条 */}
      <div style={{ height: 2, background: "linear-gradient(90deg, transparent, var(--accent), transparent)" }} />

      <div className="p-5">
        {/* 标题行 */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="text-lg">{review.emoji}</span>
            <div>
              <div className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>AI 智能分析</div>
              <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>基于全历史数据 + 多维度指标</div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold" style={{ fontFamily: "var(--font-geist-mono)", color: "var(--accent)" }}>{review.score}</div>
            <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>综合分</div>
          </div>
        </div>

        {/* 核心判断 */}
        <div className="rounded-lg p-4 mb-4" style={{ background: "var(--surface-deep)", border: "1px solid var(--surface-border)" }}>
          <div className="flex items-center gap-3 mb-2">
            <span className="text-base font-bold" style={{ color: "var(--accent)" }}>{review.verdict}</span>
            <span className="text-xs" style={{ color: "var(--text-muted)" }}>·</span>
            <span className="text-xs" style={{ color: "var(--text-secondary)" }}>{review.action}</span>
          </div>
          <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>
            👤 {review.investor_type}
            {review.manager && ` · 📋 经理：${review.manager}（${review.manager_tenure}）`}
          </div>
        </div>

        {/* 指标网格 */}
        <div className="grid grid-cols-4 gap-3 mb-4">
          {[
            { label: "成立以来", value: `+${fmt(review.summary.total_return)}%`, color: "var(--gain)" },
            { label: "年化收益", value: `${fmt(review.summary.annualized_return)}%`, color: "var(--text-primary)" },
            { label: "最大回撤", value: `-${fmt(review.summary.max_drawdown)}%`, color: "var(--gain)" },
            { label: "夏普比率", value: fmt(review.summary.sharpe_ratio, 2), color: "var(--text-primary)" },
          ].map(m => (
            <div key={m.label} className="text-center">
              <div className="text-sm font-bold" style={{ fontFamily: "var(--font-geist-mono)", color: m.color }}>{m.value}</div>
              <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>{m.label}</div>
            </div>
          ))}
        </div>

        {/* 标签 */}
        <div className="flex flex-wrap gap-2 mb-4">
          {review.tags.map((tag, i) => (
            <span key={i} className="px-2 py-0.5 rounded-full text-[10px]" style={{ background: "var(--surface-deep)", color: "var(--text-secondary)", border: "1px solid var(--surface-border)" }}>{tag}</span>
          ))}
        </div>

        {/* 优势与风险 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div className="text-[10px] font-medium mb-2" style={{ color: "var(--loss)" }}>✅ 优势</div>
            <ul className="space-y-1.5">
              {review.strengths.map((s, i) => <li key={i} className="text-xs" style={{ color: "var(--text-secondary)" }}>• {s}</li>)}
            </ul>
          </div>
          <div>
            <div className="text-[10px] font-medium mb-2" style={{ color: "var(--gain)" }}>⚠️ 风险</div>
            <ul className="space-y-1.5">
              {review.risks.map((r, i) => <li key={i} className="text-xs" style={{ color: "var(--text-secondary)" }}>• {r}</li>)}
            </ul>
          </div>
        </div>

        <div className="mt-4 pt-3 text-[10px] text-center" style={{ borderTop: "1px solid var(--surface-border)", color: "var(--text-muted)" }}>
          AI 分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。
        </div>
      </div>
    </div>
  );
}
