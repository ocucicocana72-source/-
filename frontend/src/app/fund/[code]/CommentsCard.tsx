/* 基民评论卡片 — 暗色终端风格 */
"use client";
import { useState, useEffect } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
interface Comment { content: string; author: string; time: string; reads: string; replies: string; likes: number; source: string; is_top: boolean; }
interface Analysis { summary: string; sentiment: string; emoji: string; pos_ratio: number; neg_ratio: number; key_opinions: {opinion: string; likes: number; author: string}[]; ai_insight: string; total_comments: number; }

const cardStyle = { background: "var(--surface-card)", border: "1px solid var(--surface-border)" };

export default function CommentsCard({ code }: { code: string }) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/comments/${code}?limit=10`)
      .then(r => r.json())
      .then(d => { setComments(d.comments || []); setAnalysis(d.analysis || null); })
      .catch(() => {}).finally(() => setLoading(false));
  }, [code]);

  if (loading) return <div className="rounded-lg p-5 text-center text-sm" style={{ ...cardStyle, color: "var(--text-muted)" }}>加载评论中...</div>;
  if (!comments.length) return null;

  return (
    <div className="space-y-4">
      {/* AI 整合分析 */}
      {analysis && (
        <div className="rounded-lg p-5" style={{ ...cardStyle, borderLeft: "3px solid var(--accent)" }}>
          <div className="flex items-center gap-2 mb-3">
            <span className="text-base">{analysis.emoji}</span>
            <span className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>基民情绪 AI 分析</span>
            <span className="text-[10px] px-2 py-0.5 rounded-full"
              style={analysis.pos_ratio > 60 ? { background: "rgba(255,77,79,0.1)", color: "var(--gain)" } :
                analysis.neg_ratio > 60 ? { background: "rgba(0,196,140,0.1)", color: "var(--loss)" } :
                { background: "var(--surface-deep)", color: "var(--text-muted)" }}>
              {analysis.sentiment}
            </span>
          </div>

          {/* 情绪条 */}
          <div className="flex items-center gap-2 mb-3">
            <span className="text-[10px]" style={{ color: "var(--gain)" }}>看多 {analysis.pos_ratio}%</span>
            <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: "var(--surface-deep)" }}>
              <div className="h-full rounded-full" style={{ width: `${analysis.pos_ratio}%`, background: "var(--gain)" }} />
            </div>
            <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: "var(--surface-deep)" }}>
              <div className="h-full rounded-full" style={{ width: `${analysis.neg_ratio}%`, background: "var(--loss)" }} />
            </div>
            <span className="text-[10px]" style={{ color: "var(--loss)" }}>看空 {analysis.neg_ratio}%</span>
          </div>

          <div className="text-xs leading-relaxed mb-3" style={{ color: "var(--text-secondary)" }}>{analysis.summary}</div>

          {analysis.key_opinions.length > 0 && (
            <div className="mb-3">
              <div className="text-[10px] mb-2" style={{ color: "var(--text-muted)" }}>🔥 高赞观点：</div>
              {analysis.key_opinions.map((op, i) => (
                <div key={i} className="text-[10px] pl-3 mb-1.5" style={{ color: "var(--text-secondary)", borderLeft: "2px solid var(--accent-dim)" }}>
                  &ldquo;{op.opinion}&rdquo; <span style={{ color: "var(--text-muted)" }}>— {op.author} 👍{op.likes}</span>
                </div>
              ))}
            </div>
          )}

          <div className="rounded-lg p-3" style={{ background: "var(--surface-deep)", border: "1px solid var(--surface-border)" }}>
            <div className="text-[10px] font-medium mb-1" style={{ color: "var(--accent)" }}>{analysis.ai_insight.split("：")[0]}：</div>
            <div className="text-xs" style={{ color: "var(--text-secondary)" }}>{analysis.ai_insight.split("：").slice(1).join("：")}</div>
          </div>
        </div>
      )}

      {/* 评论列表 */}
      <div className="rounded-lg p-5" style={cardStyle}>
        <div className="flex items-center gap-2 mb-4">
          <span className="text-base">💬</span>
          <span className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>基民热议</span>
          <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>{comments.length} 条</span>
        </div>
        <div className="space-y-2">
          {comments.map((c, i) => (
            <div key={i} className="p-3 rounded-lg text-xs" style={c.is_top ? { background: "rgba(212,168,67,0.08)", border: "1px solid var(--accent-dim)" } : { background: "var(--surface-deep)" }}>
              <div style={{ color: "var(--text-primary)" }}>{c.content}</div>
              <div className="flex items-center gap-3 mt-1.5">
                <span style={{ color: "var(--text-muted)" }}>{c.author}</span>
                <span style={{ color: "var(--text-muted)" }}>{c.time}</span>
                {c.is_top && <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: "rgba(212,168,67,0.15)", color: "var(--accent)" }}>🔥 热门</span>}
                <span className="ml-auto" style={{ color: "var(--text-muted)" }}>👍 {c.likes}</span>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-3 text-[10px] text-center" style={{ color: "var(--text-muted)" }}>评论来自公开讨论区，AI 分析仅供参考</div>
      </div>
    </div>
  );
}
