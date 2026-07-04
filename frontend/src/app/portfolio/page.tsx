/* 持仓监控仪表盘 — 图片识别 + 智能买卖信号 + 详细AI分析 */
"use client";
import { useState, useEffect, useRef } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
interface Dimension { score: number; label: string; desc: string; }
interface RiskMetrics { volatility: number; max_dd: number; calmar: number; downside_risk: number; win_rate: number; }
interface TrendMetrics { ret_1w: number; ret_1m: number; ret_3m: number; ret_6m: number; ret_1y: number; ma5: number; ma20: number; ma60: number; trend_direction: string; }
interface Holding {
  code: string; name: string; shares: number; current_nav: number; buy_price: number;
  profit_pct: number; total_score: number; signal: string; signal_text: string; advice: string;
  current_dd: number; week_return: number; dimensions: Record<string, Dimension>;
  risk_metrics?: RiskMetrics; trend_metrics?: TrendMetrics; ai_report?: string; error?: string;
}
interface RecognizedFund { code: string; name: string; buy_price: number; shares: number; profit_pct: number; }
interface PortfolioData { holdings: Holding[]; summary: { total_value: number; total_cost: number; total_return: number; count: number; }; }

const cardStyle = { background: "var(--surface-card)", border: "1px solid var(--surface-border)" };
const inputCls = "px-3 py-2 rounded-lg text-sm outline-none";
const inputStyle = { background: "var(--surface-card)", color: "var(--text-primary)", border: "1px solid var(--surface-border)" };

export default function PortfolioPage() {
  const [data, setData] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [addCode, setAddCode] = useState("");
  const [addPrice, setAddPrice] = useState("");
  const [addShares, setAddShares] = useState("");
  const [addDate, setAddDate] = useState("");
  const [expandedCode, setExpandedCode] = useState<string | null>(null);
  const [showReport, setShowReport] = useState<string | null>(null);

  // 图片上传相关
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<{ success: boolean; message: string; funds?: any[] } | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function fetchPortfolio() {
    setLoading(true);
    try { const res = await fetch(`${API}/api/portfolio/`); const d = await res.json(); setData(d); }
    catch {} finally { setLoading(false); }
  }
  useEffect(() => { fetchPortfolio(); }, []);

  async function handleAdd() {
    if (!addCode || !addPrice) return;
    await fetch(`${API}/api/portfolio/add`, { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code: addCode, buy_price: parseFloat(addPrice), shares: parseFloat(addShares) || 0, buy_date: addDate }) });
    setAddCode(""); setAddPrice(""); setAddShares(""); setAddDate(""); setShowAdd(false); fetchPortfolio();
  }
  async function handleRemove(code: string) {
    await fetch(`${API}/api/portfolio/${code}`, { method: "DELETE" }); fetchPortfolio();
  }
  function scoreColor(s: number) {
    return s > 0.6 ? "var(--loss)" : s > 0.2 ? "var(--accent)" : s > -0.2 ? "var(--text-secondary)" : s > -0.6 ? "#FB923C" : "var(--gain)";
  }

  // 图片上传处理
  async function handleFileUpload(file: File) {
    if (!file) return;
    const allowedTypes = ["image/jpeg", "image/png", "image/webp", "image/gif"];
    if (!allowedTypes.includes(file.type)) {
      setUploadResult({ success: false, message: "请上传图片文件（JPG, PNG, WEBP, GIF）" });
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setUploadResult({ success: false, message: "文件大小不能超过10MB" });
      return;
    }

    // 预览
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    setUploading(true);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`${API}/api/portfolio/upload`, { method: "POST", body: formData });
      const result = await res.json();
      setUploadResult(result);
      if (result.success) {
        fetchPortfolio();
        setTimeout(() => { setPreviewUrl(null); setUploadResult(null); }, 3000);
      }
    } catch (err) {
      setUploadResult({ success: false, message: "上传失败，请重试" });
    } finally {
      setUploading(false);
    }
  }

  function handleDragOver(e: React.DragEvent) { e.preventDefault(); setIsDragging(true); }
  function handleDragLeave() { setIsDragging(false); }
  function handleDrop(e: React.DragEvent) {
    e.preventDefault(); setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileUpload(file);
  }

  if (loading) return <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--surface-deep)", color: "var(--text-muted)" }}>加载中...</div>;

  const summary = data?.summary || { total_value: 0, total_cost: 0, total_return: 0, count: 0 };
  const profit = summary.total_value - summary.total_cost;

  return (
    <div className="min-h-screen" style={{ background: "var(--surface-deep)", color: "var(--text-primary)" }}>
      <div className="max-w-6xl mx-auto px-4 py-6">
        <header className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <Link href="/" className="text-xs" style={{ color: "var(--info)" }}>← 返回首页</Link>
              <h1 className="text-xl font-bold mt-2" style={{ fontFamily: "var(--font-serif), serif" }}>📊 我的持仓</h1>
              <p className="text-[10px] mt-1" style={{ color: "var(--text-muted)" }}>截图识别 · AI 智能信号 · 详细分析报告</p>
            </div>
            <div className="flex gap-2">
              <button onClick={() => setShowAdd(!showAdd)} className="px-4 py-2 rounded-lg text-sm font-medium" style={{ background: "var(--surface-card)", border: "1px solid var(--surface-border)" }}>手动添加</button>
              <button onClick={() => fileInputRef.current?.click()} className="px-4 py-2 rounded-lg text-sm font-medium text-black" style={{ background: "var(--accent)" }}>📷 截图识别</button>
            </div>
          </div>
          <div className="divider-gold" />
        </header>

        {/* 图片上传区域 */}
        <div className="mb-5">
          <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={e => { const f = e.target.files?.[0]; if (f) handleFileUpload(f); }} />
          <div
            className="rounded-lg p-6 text-center cursor-pointer transition-all"
            style={{
              ...cardStyle,
              border: isDragging ? "2px dashed var(--accent)" : "2px dashed var(--surface-border)",
              background: isDragging ? "rgba(212, 168, 67, 0.05)" : "var(--surface-card)",
            }}
            onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            {previewUrl ? (
              <div className="relative inline-block">
                <img src={previewUrl} alt="预览" className="max-h-48 rounded-lg mx-auto" style={{ border: "1px solid var(--surface-border)" }} />
                {uploading && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-lg">
                    <div className="text-sm" style={{ color: "var(--accent)" }}>识别中...</div>
                  </div>
                )}
              </div>
            ) : (
              <div>
                <div className="text-3xl mb-2">📷</div>
                <div className="text-sm" style={{ color: "var(--text-secondary)" }}>拖拽支付宝持仓截图到此处，或点击上传</div>
                <div className="text-[10px] mt-1" style={{ color: "var(--text-muted)" }}>支持 JPG, PNG, WEBP, GIF · 最大 10MB</div>
              </div>
            )}
          </div>
          {uploadResult && (
            <div className="mt-3 rounded-lg p-3 text-sm" style={{
              background: uploadResult.success ? "rgba(0, 196, 140, 0.1)" : "rgba(255, 77, 79, 0.1)",
              border: `1px solid ${uploadResult.success ? "var(--loss)" : "var(--gain)"}`,
              color: uploadResult.success ? "var(--loss)" : "var(--gain)",
            }}>
              {uploadResult.message}
            </div>
          )}
        </div>

        {/* 总览 */}
        <div className="rounded-lg p-5 mb-5" style={cardStyle}>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[{ l: "持仓数量", v: `${summary.count} 只` }, { l: "总市值", v: `¥${summary.total_value.toLocaleString()}` }, { l: "总成本", v: `¥${summary.total_cost.toLocaleString()}` }, { l: "总收益", v: `${profit >= 0 ? "+" : ""}¥${profit.toFixed(2)} (${summary.total_return >= 0 ? "+" : ""}${summary.total_return.toFixed(2)}%)`, c: profit >= 0 ? "var(--gain)" : "var(--loss)" }].map(m => (
              <div key={m.l}><div className="text-[10px]" style={{ color: "var(--text-muted)" }}>{m.l}</div><div className="text-lg font-bold" style={{ fontFamily: "var(--font-geist-mono)", color: m.c || "var(--text-primary)" }}>{m.v}</div></div>
            ))}
          </div>
        </div>

        {/* 手动添加表单 */}
        {showAdd && (
          <div className="rounded-lg p-5 mb-5" style={{ ...cardStyle, borderLeft: "3px solid var(--accent)" }}>
            <div className="text-sm font-bold mb-3" style={{ color: "var(--accent)" }}>手动添加持仓</div>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <input placeholder="基金代码" value={addCode} onChange={e => setAddCode(e.target.value)} className={inputCls} style={inputStyle} />
              <input placeholder="买入价" type="number" value={addPrice} onChange={e => setAddPrice(e.target.value)} className={inputCls} style={inputStyle} />
              <input placeholder="份额(可选)" type="number" value={addShares} onChange={e => setAddShares(e.target.value)} className={inputCls} style={inputStyle} />
              <input placeholder="买入日期" type="date" value={addDate} onChange={e => setAddDate(e.target.value)} className={inputCls} style={inputStyle} />
              <button onClick={handleAdd} className="px-4 py-2 rounded-lg text-sm font-medium text-black" style={{ background: "var(--accent)" }}>确认添加</button>
            </div>
          </div>
        )}

        {/* 持仓列表 */}
        {!data?.holdings?.length ? (
          <div className="rounded-lg p-12 text-center" style={cardStyle}>
            <div className="text-3xl mb-3">📭</div>
            <div className="text-sm" style={{ color: "var(--text-muted)" }}>暂无持仓</div>
            <div className="text-xs mt-2" style={{ color: "var(--text-muted)" }}>上传支付宝截图或手动添加基金开始监控</div>
          </div>
        ) : (
          <div className="space-y-3">
            {data.holdings.map(h => {
              const isExpanded = expandedCode === h.code;
              const profitColor = h.profit_pct >= 0 ? "var(--gain)" : "var(--loss)";
              if (h.error) return (
                <div key={h.code} className="rounded-lg p-4 flex items-center gap-3" style={cardStyle}>
                  <span style={{ fontFamily: "var(--font-geist-mono)", color: "var(--accent)" }}>{h.code}</span>
                  <span className="text-sm" style={{ color: "var(--text-muted)" }}>{h.name}</span>
                  <span className="text-xs" style={{ color: "var(--gain)" }}>{h.error}</span>
                  <button onClick={() => handleRemove(h.code)} className="ml-auto text-xs" style={{ color: "var(--text-muted)" }}>删除</button>
                </div>
              );
              return (
                <div key={h.code} className="rounded-lg overflow-hidden" style={cardStyle}>
                  <div className="p-4 flex items-center gap-4 cursor-pointer" onClick={() => setExpandedCode(isExpanded ? null : h.code)}
                    onMouseEnter={e => (e.currentTarget.style.background = "var(--surface-hover)")} onMouseLeave={e => (e.currentTarget.style.background = "transparent")}>
                    <div className="text-xl">{h.signal}</div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2"><span className="text-sm font-bold truncate">{h.name}</span><span className="text-[10px]" style={{ fontFamily: "var(--font-geist-mono)", color: "var(--text-muted)" }}>{h.code}</span></div>
                      <div className="text-[10px] mt-0.5" style={{ color: "var(--text-muted)" }}>{h.signal_text} · {h.advice}</div>
                    </div>
                    <div className="text-right shrink-0">
                      <div className="text-sm font-bold" style={{ fontFamily: "var(--font-geist-mono)", color: profitColor }}>{h.profit_pct >= 0 ? "+" : ""}{h.profit_pct.toFixed(2)}%</div>
                      <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>净值 {h.current_nav}</div>
                    </div>
                    <div className="shrink-0">
                      <div className="text-lg font-bold" style={{ fontFamily: "var(--font-geist-mono)", color: scoreColor(h.total_score) }}>{h.total_score > 0 ? "+" : ""}{h.total_score.toFixed(2)}</div>
                      <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>综合分</div>
                    </div>
                    <button onClick={e => { e.stopPropagation(); handleRemove(h.code); }} className="text-xs shrink-0" style={{ color: "var(--text-muted)" }}>×</button>
                  </div>
                  {isExpanded && (
                    <div className="px-4 pb-4 space-y-4" style={{ borderTop: "1px solid var(--surface-border)" }}>
                      {/* 五维度分析 */}
                      <div className="pt-3">
                        <div className="text-[10px] font-medium mb-2" style={{ color: "var(--text-muted)" }}>📊 五维度评分</div>
                        <div className="grid grid-cols-5 gap-2">
                          {Object.entries(h.dimensions).map(([key, dim]) => {
                            const barWidth = ((dim.score + 1) / 2) * 100;
                            const barColor = dim.score > 0.3 ? "var(--loss)" : dim.score < -0.3 ? "var(--gain)" : "var(--text-muted)";
                            return (<div key={key}>
                              <div className="text-[10px] mb-1" style={{ color: "var(--text-muted)" }}>{dim.label}</div>
                              <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "var(--surface-deep)" }}><div className="h-full rounded-full" style={{ width: `${barWidth}%`, background: barColor }} /></div>
                              <div className="text-[10px] mt-0.5 font-medium" style={{ fontFamily: "var(--font-geist-mono)", color: barColor }}>{dim.score > 0 ? "+" : ""}{dim.score}</div>
                              <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>{dim.desc}</div>
                            </div>);
                          })}
                        </div>
                      </div>

                      {/* 详细指标 */}
                      <div className="flex flex-wrap gap-4 text-xs" style={{ color: "var(--text-secondary)" }}>
                        <span>买入价：<b style={{ fontFamily: "var(--font-geist-mono)" }}>{h.buy_price}</b></span>
                        <span>现价：<b style={{ fontFamily: "var(--font-geist-mono)" }}>{h.current_nav}</b></span>
                        <span>回撤：<b style={{ fontFamily: "var(--font-geist-mono)", color: "var(--gain)" }}>{h.current_dd}%</b></span>
                        <span>近1周：<b style={{ fontFamily: "var(--font-geist-mono)", color: h.week_return >= 0 ? "var(--gain)" : "var(--loss)" }}>{h.week_return >= 0 ? "+" : ""}{h.week_return}%</b></span>
                        {h.shares > 0 && <span>份额：<b style={{ fontFamily: "var(--font-geist-mono)" }}>{h.shares}</b></span>}
                      </div>

                      {/* 风险指标 */}
                      {h.risk_metrics && (
                        <div className="rounded-lg p-3" style={{ background: "var(--surface-deep)", border: "1px solid var(--surface-border)" }}>
                          <div className="text-[10px] font-medium mb-2" style={{ color: "var(--text-muted)" }}>⚠️ 风险指标</div>
                          <div className="grid grid-cols-5 gap-2 text-xs">
                            <div><div style={{ color: "var(--text-muted)" }}>波动率</div><div className="font-bold" style={{ fontFamily: "var(--font-geist-mono)" }}>{h.risk_metrics.volatility}%</div></div>
                            <div><div style={{ color: "var(--text-muted)" }}>最大回撤</div><div className="font-bold" style={{ fontFamily: "var(--font-geist-mono)", color: "var(--gain)" }}>{h.risk_metrics.max_dd}%</div></div>
                            <div><div style={{ color: "var(--text-muted)" }}>卡玛比率</div><div className="font-bold" style={{ fontFamily: "var(--font-geist-mono)" }}>{h.risk_metrics.calmar}</div></div>
                            <div><div style={{ color: "var(--text-muted)" }}>下行风险</div><div className="font-bold" style={{ fontFamily: "var(--font-geist-mono)" }}>{h.risk_metrics.downside_risk}%</div></div>
                            <div><div style={{ color: "var(--text-muted)" }}>胜率</div><div className="font-bold" style={{ fontFamily: "var(--font-geist-mono)" }}>{h.risk_metrics.win_rate}%</div></div>
                          </div>
                        </div>
                      )}

                      {/* 趋势指标 */}
                      {h.trend_metrics && (
                        <div className="rounded-lg p-3" style={{ background: "var(--surface-deep)", border: "1px solid var(--surface-border)" }}>
                          <div className="text-[10px] font-medium mb-2" style={{ color: "var(--text-muted)" }}>📈 趋势指标</div>
                          <div className="flex flex-wrap gap-3 text-xs">
                            <span>趋势：<b style={{ color: "var(--accent)" }}>{h.trend_metrics.trend_direction}</b></span>
                            <span>1周：<b style={{ fontFamily: "var(--font-geist-mono)", color: h.trend_metrics.ret_1w >= 0 ? "var(--gain)" : "var(--loss)" }}>{h.trend_metrics.ret_1w >= 0 ? "+" : ""}{h.trend_metrics.ret_1w}%</b></span>
                            <span>1月：<b style={{ fontFamily: "var(--font-geist-mono)", color: h.trend_metrics.ret_1m >= 0 ? "var(--gain)" : "var(--loss)" }}>{h.trend_metrics.ret_1m >= 0 ? "+" : ""}{h.trend_metrics.ret_1m}%</b></span>
                            <span>3月：<b style={{ fontFamily: "var(--font-geist-mono)", color: h.trend_metrics.ret_3m >= 0 ? "var(--gain)" : "var(--loss)" }}>{h.trend_metrics.ret_3m >= 0 ? "+" : ""}{h.trend_metrics.ret_3m}%</b></span>
                          </div>
                        </div>
                      )}

                      {/* 操作建议 */}
                      <div className="rounded-lg p-3" style={{ background: "var(--surface-deep)", border: "1px solid var(--surface-border)" }}>
                        <div className="text-[10px] font-medium mb-1" style={{ color: scoreColor(h.total_score) }}>💡 {h.signal_text}</div>
                        <div className="text-xs" style={{ color: "var(--text-secondary)" }}>{h.advice}</div>
                      </div>

                      {/* 查看详细报告按钮 */}
                      {h.ai_report && (
                        <button
                          onClick={() => setShowReport(showReport === h.code ? null : h.code)}
                          className="w-full py-2 rounded-lg text-xs font-medium"
                          style={{ background: "var(--accent)", color: "black" }}
                        >
                          {showReport === h.code ? "收起详细报告" : "📊 查看AI详细分析报告"}
                        </button>
                      )}

                      {/* AI详细报告 */}
                      {showReport === h.code && h.ai_report && (
                        <div className="rounded-lg p-4" style={{ background: "var(--surface-deep)", border: "1px solid var(--accent)" }}>
                          <div className="text-xs" style={{ color: "var(--text-primary)", lineHeight: "1.8" }}>
                            {h.ai_report.split('\n').map((line, i) => {
                              // 处理粗体文本 **xxx**
                              const parts = line.split(/\*\*(.*?)\*\*/g);
                              return (
                                <div key={i} className="mb-1">
                                  {parts.map((part, j) =>
                                    j % 2 === 1
                                      ? <strong key={j} style={{ color: "var(--accent)" }}>{part}</strong>
                                      : <span key={j}>{part}</span>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
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
