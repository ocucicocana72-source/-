/* 根布局 — 暗色终端风格 */

import type { Metadata } from "next";
import { Geist_Mono, Noto_Sans_SC, Noto_Serif_SC } from "next/font/google";
import "./globals.css";

const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });
const notoSans = Noto_Sans_SC({ variable: "--font-noto-sans", subsets: ["latin"], weight: ["400", "500", "700"] });
const notoSerif = Noto_Serif_SC({ variable: "--font-noto-serif", subsets: ["latin"], weight: ["700"] });

export const metadata: Metadata = {
  title: "基金智能分析助手",
  description: "支付宝基金深度分析、投资建议、新闻聚合",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN" className={`${geistMono.variable} ${notoSans.variable} ${notoSerif.variable} antialiased`}>
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
