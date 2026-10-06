"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useOmniStore } from "../../store/omniStore";
import { fetchHistoricalKlines, CandleData } from "../../lib/api/binanceRest";
import { detectPatterns, PatternResult } from "../../lib/ai/patternDetector";
import { analyzeTrend, TrendResult } from "../../lib/ai/trendAnalyzer";
import { scanVolatility, VolatilityResult } from "../../lib/ai/volatilityScanner";
import {
  calculateSentiment,
  SentimentResult,
  SentimentInput,
} from "../../lib/ai/sentimentEngine";
import { calculateRSI } from "../../lib/indicators/rsi";
import AIDebate from "../../components/dom/AIDebate";
import { MonteCarloPredictor } from "../../components/canvas/MonteCarloPredictor";

// ─── Constants ────────────────────────────────────────────────────────────────
const CORRELATION_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT"];
const DISPLAY_NAMES = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE"];

// ─── Helper: card container ───────────────────────────────────────────────────
function GlassCard({
  children,
  className = "",
  accentColor = "#00F0FF",
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  accentColor?: string;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: "easeOut" }}
      className={`relative rounded-2xl backdrop-blur-md overflow-hidden ${className}`}
      style={{
        background: `rgba(5,5,10,0.6)`,
        border: `1px solid ${accentColor}22`,
        boxShadow: `0 0 30px ${accentColor}11, inset 0 1px 0 ${accentColor}18`,
      }}
    >
      {/* Top accent line */}
      <div
        className="absolute top-0 left-0 right-0 h-[1px]"
        style={{ background: `linear-gradient(90deg, transparent, ${accentColor}55, transparent)` }}
      />
      {children}
    </motion.div>
  );
}

// ─── Section heading ──────────────────────────────────────────────────────────
function SectionHeading({
  children,
  color = "#00F0FF",
  icon,
}: {
  children: React.ReactNode;
  color?: string;
  icon?: string;
}) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <span
        className="w-1.5 h-1.5 rounded-full animate-pulse"
        style={{ backgroundColor: color }}
      />
      {icon && <span className="text-sm">{icon}</span>}
      <span
        className="font-orbitron text-[10px] tracking-[0.25em] font-bold uppercase"
        style={{ color }}
      >
        {children}
      </span>
    </div>
  );
}

// ─── Section 1: AI Market Summary ────────────────────────────────────────────
function AIMarketSummary({
  sentiment,
  trend,
  loading,
}: {
  sentiment: SentimentResult | null;
  trend: TrendResult | null;
  loading: boolean;
}) {
  const score = sentiment?.score ?? 50;
  const color = sentiment?.color ?? "#00F0FF";

  return (
    <GlassCard accentColor={color} delay={0}>
      <div className="p-6">
        <SectionHeading color={color} icon="🧠">
          AI Market Summary
        </SectionHeading>

        {loading ? (
          <div className="flex items-center gap-3 py-4">
            <div
              className="w-4 h-4 border-2 border-t-transparent rounded-full animate-spin"
              style={{ borderColor: color }}
            />
            <span className="font-mono text-xs text-white/40">Analyzing market data…</span>
          </div>
        ) : (
          <div className="flex flex-col lg:flex-row gap-6 items-start">
            {/* Score Dial */}
            <div className="flex-shrink-0 flex flex-col items-center gap-2">
              <div className="relative w-28 h-28">
                <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="6" />
                  <motion.circle
                    cx="50"
                    cy="50"
                    r="42"
                    fill="none"
                    stroke={color}
                    strokeWidth="6"
                    strokeLinecap="round"
                    strokeDasharray="263.9"
                    initial={{ strokeDashoffset: 263.9 }}
                    animate={{ strokeDashoffset: 263.9 - (score / 100) * 263.9 }}
                    transition={{ duration: 1.2, ease: "easeOut" }}
                    style={{ filter: `drop-shadow(0 0 6px ${color})` }}
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="font-orbitron text-2xl font-black" style={{ color }}>
                    {score}
                  </span>
                  <span className="font-mono text-[8px] text-white/40 tracking-widest">SCORE</span>
                </div>
              </div>
              <span
                className="font-orbitron text-xs font-bold tracking-widest text-center"
                style={{ color }}
              >
                {sentiment?.label?.replace("_", " ") ?? "—"}
              </span>
            </div>

            {/* Summary text */}
            <div className="flex-1 space-y-3">
              <p className="font-mono text-xs leading-relaxed text-white/70">
                {sentiment?.summary ?? "Awaiting market data…"}
              </p>
              {trend && (
                <div
                  className="rounded-xl px-4 py-2 border text-xs font-mono"
                  style={{
                    borderColor: `${color}33`,
                    background: `${color}0a`,
                    color: "rgba(255,255,255,0.7)",
                  }}
                >
                  <span style={{ color }}>TREND → </span>
                  {trend.signal}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </GlassCard>
  );
}

// ─── Section 2: Pattern Detector ─────────────────────────────────────────────
function PatternDetector({
  patterns,
  loading,
}: {
  patterns: PatternResult[];
  loading: boolean;
}) {
  const recent = patterns.slice(-8).reverse().slice(0, 6);

  return (
    <GlassCard accentColor="#8B00FF" delay={0.1}>
      <div className="p-5">
        <SectionHeading color="#8B00FF" icon="🕯️">
          Pattern Detector
        </SectionHeading>

        {loading ? (
          <div className="flex items-center gap-3 py-3">
            <div className="w-4 h-4 border-2 border-t-transparent rounded-full animate-spin border-[#8B00FF]" />
            <span className="font-mono text-xs text-white/40">Scanning candlestick patterns…</span>
          </div>
        ) : recent.length === 0 ? (
          <p className="font-mono text-xs text-white/30 text-center py-4">
            No significant patterns detected
          </p>
        ) : (
          <div className="space-y-2">
            <AnimatePresence>
              {recent.map((p, i) => {
                const isBull = p.direction === "BULL";
                const isBear = p.direction === "BEAR";
                const patColor = isBull ? "#00FF66" : isBear ? "#FF0055" : "#8B00FF";
                return (
                  <motion.div
                    key={`${p.pattern}-${p.candleIndex}`}
                    initial={{ opacity: 0, x: -16 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.06 }}
                    className="flex items-center gap-3 py-1.5 border-b border-white/5"
                  >
                    <span className="text-sm">{isBull ? "🟢" : isBear ? "🔴" : "⚪"}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-baseline">
                        <span
                          className="font-orbitron text-[10px] font-bold"
                          style={{ color: patColor }}
                        >
                          {p.pattern}
                        </span>
                        <span className="font-mono text-[9px] text-white/30">
                          idx {p.candleIndex}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
                          <motion.div
                            className="h-full rounded-full"
                            initial={{ width: 0 }}
                            animate={{ width: `${p.confidence * 100}%` }}
                            transition={{ duration: 0.6, delay: i * 0.06 }}
                            style={{ backgroundColor: patColor }}
                          />
                        </div>
                        <span
                          className="font-mono text-[9px] font-bold w-10 text-right"
                          style={{ color: patColor }}
                        >
                          {(p.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        )}
      </div>
    </GlassCard>
  );
}

// ─── Section 3: Volatility Scanner ───────────────────────────────────────────
function VolatilityScanner({
  volatility,
  loading,
}: {
  volatility: VolatilityResult | null;
  loading: boolean;
}) {
  const state = volatility?.state ?? "NORMAL";
  const width = volatility?.width ?? 0;
  const prob = volatility?.breakoutProbability ?? 0;
  const isSqueeze = state === "SQUEEZE";
  const isExpansion = state === "EXPANSION";
  const stateColor = isSqueeze ? "#FF5500" : isExpansion ? "#00FF66" : "#00F0FF";

  const gaugeAngle = Math.min(180, prob * 180); // 0° = 0 probability, 180° = 100%

  return (
    <GlassCard accentColor={stateColor} delay={0.2}>
      <div className="p-5">
        <SectionHeading color={stateColor} icon="📡">
          Volatility Scanner
        </SectionHeading>

        {loading ? (
          <div className="flex items-center gap-3 py-3">
            <div
              className="w-4 h-4 border-2 border-t-transparent rounded-full animate-spin"
              style={{ borderColor: stateColor }}
            />
            <span className="font-mono text-xs text-white/40">Calculating BB width…</span>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Gauge */}
            <div className="flex flex-col items-center gap-2">
              <div className="relative w-32 h-16 overflow-hidden">
                <svg viewBox="0 0 120 60" className="w-full h-full">
                  {/* Background arc */}
                  <path
                    d="M 10 55 A 50 50 0 0 1 110 55"
                    fill="none"
                    stroke="rgba(255,255,255,0.06)"
                    strokeWidth="8"
                    strokeLinecap="round"
                  />
                  {/* Colored arc */}
                  <motion.path
                    d="M 10 55 A 50 50 0 0 1 110 55"
                    fill="none"
                    stroke={stateColor}
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray="157"
                    initial={{ strokeDashoffset: 157 }}
                    animate={{ strokeDashoffset: 157 - (prob * 157) }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    style={{ filter: `drop-shadow(0 0 4px ${stateColor})` }}
                  />
                  {/* Needle */}
                  <motion.line
                    x1="60"
                    y1="55"
                    x2="60"
                    y2="12"
                    stroke="white"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    initial={{ rotate: -90, originX: "60px", originY: "55px" }}
                    animate={{ rotate: gaugeAngle - 90, originX: "60px", originY: "55px" }}
                    transition={{ duration: 1.2, ease: "easeOut" }}
                    style={{ transformOrigin: "60px 55px" }}
                  />
                  <circle cx="60" cy="55" r="3" fill={stateColor} />
                </svg>
              </div>

              {/* SQUEEZE label */}
              <AnimatePresence>
                {isSqueeze && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: [0.6, 1, 0.6], scale: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                    className="font-orbitron text-xs font-black tracking-widest text-center"
                    style={{ color: "#FF5500", textShadow: "0 0 20px #FF5500" }}
                  >
                    ⚡ BREAKOUT IMMINENT
                  </motion.div>
                )}
                {isExpansion && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="font-orbitron text-xs font-black tracking-widest"
                    style={{ color: "#00FF66" }}
                  >
                    🚀 EXPANSION ACTIVE
                  </motion.div>
                )}
              </AnimatePresence>

              <div className="flex items-center gap-4 text-center">
                <div>
                  <div className="font-orbitron text-xs font-bold" style={{ color: stateColor }}>
                    {state}
                  </div>
                  <div className="font-mono text-[9px] text-white/30">STATE</div>
                </div>
                <div>
                  <div className="font-orbitron text-xs font-bold text-white">
                    {(width * 100).toFixed(2)}%
                  </div>
                  <div className="font-mono text-[9px] text-white/30">BB WIDTH</div>
                </div>
                <div>
                  <div
                    className="font-orbitron text-xs font-bold"
                    style={{ color: stateColor }}
                  >
                    {(prob * 100).toFixed(0)}%
                  </div>
                  <div className="font-mono text-[9px] text-white/30">BREAKOUT PROB</div>
                </div>
              </div>
            </div>

            <p className="font-mono text-[9px] leading-relaxed text-white/40 border-t border-white/5 pt-3">
              {volatility?.signal}
            </p>
          </div>
        )}
      </div>
    </GlassCard>
  );
}

// ─── Section 4: Trend Compass ─────────────────────────────────────────────────
function TrendCompass({ trend, loading }: { trend: TrendResult | null; loading: boolean }) {
  const direction = trend?.direction ?? "NEUTRAL";
  const strength = trend?.strength ?? 0;
  const smaCross = trend?.smaCross ?? "NONE";

  const directionMap: Record<string, { angle: number; color: string; label: string }> = {
    STRONG_BULL: { angle: 90, color: "#00FF66", label: "STRONG BULL" },
    BULL: { angle: 45, color: "#00F0FF", label: "BULL" },
    NEUTRAL: { angle: 0, color: "#8B00FF", label: "NEUTRAL" },
    BEAR: { angle: -45, color: "#FF5500", label: "BEAR" },
    STRONG_BEAR: { angle: -90, color: "#FF0055", label: "STRONG BEAR" },
  };

  const current = directionMap[direction] ?? directionMap.NEUTRAL;

  return (
    <GlassCard accentColor={current.color} delay={0.15}>
      <div className="p-5">
        <SectionHeading color={current.color} icon="🧭">
          Trend Compass
        </SectionHeading>

        {loading ? (
          <div className="flex items-center gap-3 py-3">
            <div
              className="w-4 h-4 border-2 border-t-transparent rounded-full animate-spin"
              style={{ borderColor: current.color }}
            />
            <span className="font-mono text-xs text-white/40">Computing SMAs…</span>
          </div>
        ) : (
          <div className="flex items-center gap-6">
            {/* Compass rose */}
            <div className="relative flex-shrink-0 w-24 h-24">
              {/* Outer ring */}
              <div
                className="absolute inset-0 rounded-full border-2"
                style={{
                  borderColor: `${current.color}33`,
                  boxShadow: `0 0 20px ${current.color}22`,
                }}
              />
              {/* Cardinal labels */}
              {["N", "E", "S", "W"].map((label, i) => {
                const a = (i * 90 * Math.PI) / 180;
                const r = 38;
                const cx = 48 + r * Math.sin(a);
                const cy = 48 - r * Math.cos(a);
                return (
                  <span
                    key={label}
                    className="absolute font-mono text-[7px] text-white/20"
                    style={{ left: cx - 4, top: cy - 4 }}
                  >
                    {label}
                  </span>
                );
              })}
              {/* Needle */}
              <div className="absolute inset-0 flex items-center justify-center">
                <motion.div
                  animate={{ rotate: current.angle }}
                  transition={{ duration: 0.8, ease: "easeOut" }}
                  className="relative w-1 h-16"
                >
                  <div
                    className="absolute top-0 left-1/2 -translate-x-1/2 w-0.5 h-8 rounded-full"
                    style={{
                      background: current.color,
                      boxShadow: `0 0 8px ${current.color}`,
                    }}
                  />
                  <div
                    className="absolute bottom-0 left-1/2 -translate-x-1/2 w-0.5 h-8 rounded-full"
                    style={{ background: "rgba(255,255,255,0.15)" }}
                  />
                </motion.div>
                <div
                  className="absolute w-3 h-3 rounded-full border-2"
                  style={{ borderColor: current.color, backgroundColor: "#05050A" }}
                />
              </div>
            </div>

            {/* Metrics */}
            <div className="flex-1 space-y-3">
              <div>
                <div
                  className="font-orbitron text-lg font-black tracking-wider"
                  style={{ color: current.color, textShadow: `0 0 12px ${current.color}` }}
                >
                  {current.label}
                </div>
                <div className="font-mono text-[9px] text-white/30 mt-0.5">TREND DIRECTION</div>
              </div>

              {/* Strength bar */}
              <div>
                <div className="flex justify-between font-mono text-[9px] text-white/40 mb-1">
                  <span>STRENGTH</span>
                  <span style={{ color: current.color }}>{strength}%</span>
                </div>
                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${strength}%` }}
                    transition={{ duration: 0.9, ease: "easeOut" }}
                    style={{ backgroundColor: current.color, boxShadow: `0 0 6px ${current.color}` }}
                  />
                </div>
              </div>

              {/* SMA Cross Badge */}
              {smaCross !== "NONE" && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg"
                  style={{
                    background: smaCross === "GOLDEN" ? "#00FF6615" : "#FF005515",
                    border: `1px solid ${smaCross === "GOLDEN" ? "#00FF6644" : "#FF005544"}`,
                  }}
                >
                  <span className="text-xs">{smaCross === "GOLDEN" ? "⭐" : "💀"}</span>
                  <span
                    className="font-orbitron text-[9px] font-bold"
                    style={{ color: smaCross === "GOLDEN" ? "#00FF66" : "#FF0055" }}
                  >
                    {smaCross} CROSS
                  </span>
                </motion.div>
              )}
            </div>
          </div>
        )}
      </div>
    </GlassCard>
  );
}

// ─── Section 5: Asset Correlation Matrix ─────────────────────────────────────
function CorrelationMatrix({
  tickers,
}: {
  tickers: Record<string, { price: string; open: string }>;
}) {
  // Compute simplified 24h price-change correlations
  const changes = CORRELATION_SYMBOLS.map((sym) => {
    const t = tickers[sym];
    if (!t) return 0;
    const price = parseFloat(t.price);
    const open = parseFloat(t.open);
    if (open === 0) return 0;
    return ((price - open) / open) * 100;
  });

  // Build pseudo-correlation: how similar two assets' directions are
  function corr(i: number, j: number): number {
    if (i === j) return 1;
    const a = changes[i];
    const b = changes[j];
    if (a === 0 && b === 0) return 0;
    // sign agreement + magnitude proximity
    const signMatch = Math.sign(a) === Math.sign(b) ? 1 : -1;
    const denom = Math.max(Math.abs(a), Math.abs(b), 0.001);
    const magSim = 1 - Math.abs(Math.abs(a) - Math.abs(b)) / denom;
    return parseFloat((signMatch * magSim).toFixed(2));
  }

  function corrColor(v: number): string {
    if (v >= 0.7) return "#00FF66";
    if (v >= 0.3) return "#00F0FF";
    if (v >= -0.3) return "#8B00FF";
    if (v >= -0.7) return "#FF5500";
    return "#FF0055";
  }

  return (
    <GlassCard accentColor="#00F0FF" delay={0.25}>
      <div className="p-5">
        <SectionHeading color="#00F0FF" icon="🔗">
          Asset Correlation Matrix
        </SectionHeading>

        <div className="overflow-x-auto">
          <table className="w-full text-center" style={{ borderCollapse: "separate", borderSpacing: "2px" }}>
            <thead>
              <tr>
                <td className="w-8" />
                {DISPLAY_NAMES.map((name) => (
                  <th
                    key={name}
                    className="font-orbitron text-[8px] text-white/40 pb-1 w-10"
                  >
                    {name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {DISPLAY_NAMES.map((rowName, i) => (
                <tr key={rowName}>
                  <td className="font-orbitron text-[8px] text-white/40 pr-1 text-right">{rowName}</td>
                  {DISPLAY_NAMES.map((_, j) => {
                    const v = corr(i, j);
                    const bg = corrColor(v);
                    return (
                      <td key={j} className="p-0.5">
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: (i * 6 + j) * 0.02 }}
                          className="w-8 h-8 rounded-md flex items-center justify-center cursor-default"
                          style={{
                            backgroundColor: `${bg}22`,
                            border: `1px solid ${bg}33`,
                          }}
                          title={`${rowName}/${DISPLAY_NAMES[j]}: ${v.toFixed(2)}`}
                        >
                          <span
                            className="font-mono text-[8px] font-bold"
                            style={{ color: bg }}
                          >
                            {i === j ? "—" : v.toFixed(1)}
                          </span>
                        </motion.div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>

          {/* Legend */}
          <div className="flex items-center gap-3 mt-3 flex-wrap">
            {[
              { color: "#00FF66", label: "Strong Positive" },
              { color: "#00F0FF", label: "Positive" },
              { color: "#8B00FF", label: "Neutral" },
              { color: "#FF5500", label: "Negative" },
              { color: "#FF0055", label: "Strong Negative" },
            ].map(({ color, label }) => (
              <div key={label} className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-sm" style={{ backgroundColor: color }} />
                <span className="font-mono text-[7px] text-white/30">{label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </GlassCard>
  );
}

// ─── Section 6: Whale Intelligence ───────────────────────────────────────────
function WhaleIntelligence({
  whaleAlerts,
  toasts,
}: {
  whaleAlerts: { id: string; token: string; amountUsd: string; from: string; to: string; time: number }[];
  toasts: { id: string; title: string; message: string; type: string }[];
}) {
  const whaleCount = toasts.filter((t) => t.type === "whale").length;
  const rektCount = toasts.filter((t) => t.type === "rekt").length;

  // Simplified accumulation/distribution: more whale buys vs rekt events
  const sentiment = whaleCount > rektCount ? "ACCUMULATING" : whaleCount < rektCount ? "DISTRIBUTING" : "BALANCED";
  const sentColor = sentiment === "ACCUMULATING" ? "#00FF66" : sentiment === "DISTRIBUTING" ? "#FF0055" : "#8B00FF";
  const pressure = Math.min(100, Math.max(0, (whaleCount / (whaleCount + rektCount + 1)) * 100));

  return (
    <GlassCard accentColor="#00F0FF" delay={0.3}>
      <div className="p-5">
        <SectionHeading color="#00F0FF" icon="🐋">
          Whale Intelligence
        </SectionHeading>

        <div className="flex flex-col lg:flex-row gap-4">
          {/* Pressure Gauge */}
          <div className="flex-shrink-0 space-y-3">
            <div className="flex items-center gap-3">
              <div className="text-center">
                <motion.div
                  animate={{
                    textShadow: [
                      `0 0 8px ${sentColor}`,
                      `0 0 20px ${sentColor}`,
                      `0 0 8px ${sentColor}`,
                    ],
                  }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="font-orbitron text-base font-black"
                  style={{ color: sentColor }}
                >
                  {sentiment}
                </motion.div>
                <div className="font-mono text-[9px] text-white/30">WHALE POSTURE</div>
              </div>
            </div>

            {/* Buy/Sell pressure bar */}
            <div>
              <div className="flex justify-between font-mono text-[8px] mb-1">
                <span style={{ color: "#00FF66" }}>BUY {whaleCount}</span>
                <span style={{ color: "#FF0055" }}>SELL {rektCount}</span>
              </div>
              <div className="h-2 bg-[#FF005522] rounded-full overflow-hidden relative">
                <motion.div
                  className="h-full rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${pressure}%` }}
                  transition={{ duration: 0.8 }}
                  style={{ background: "linear-gradient(90deg, #00FF66, #00F0FF)" }}
                />
              </div>
            </div>
          </div>

          {/* Alert list */}
          <div className="flex-1 min-w-0">
            {whaleAlerts.length === 0 ? (
              <p className="font-mono text-[9px] text-white/20 text-center py-4">
                Monitoring whale wallets…
              </p>
            ) : (
              <div className="space-y-1.5 max-h-[140px] overflow-y-auto">
                {whaleAlerts.slice(0, 8).map((alert) => (
                  <motion.div
                    key={alert.id}
                    initial={{ opacity: 0, x: 12 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="flex items-center gap-2 py-1 border-b border-white/5 text-[9px] font-mono"
                  >
                    <span className="text-[#00F0FF] font-bold w-12 truncate">{alert.token}</span>
                    <span className="text-white flex-1 truncate">{alert.amountUsd}</span>
                    <span className="text-white/30 truncate max-w-[80px]">{alert.from}</span>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </GlassCard>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function IntelligencePage() {
  // Store
  const tickers = useOmniStore((s) => s.tickers);
  const whaleAlerts = useOmniStore((s) => s.whaleAlerts);
  const toasts = useOmniStore((s) => s.toasts);
  const chartSymbol = useOmniStore((s) => s.chartSymbol);
  const latestCandle = useOmniStore((s) => s.latestCandle);

  // Historical candles state
  const [candles, setCandles] = useState<CandleData[]>([]);
  const [loading, setLoading] = useState(true);

  // AI results
  const [patterns, setPatterns] = useState<PatternResult[]>([]);
  const [trend, setTrend] = useState<TrendResult | null>(null);
  const [volatility, setVolatility] = useState<VolatilityResult | null>(null);
  const [sentiment, setSentiment] = useState<SentimentResult | null>(null);
  const [fearGreedScore, setFearGreedScore] = useState(50);

  // Ref to keep stable candles during updates
  const candlesRef = useRef<CandleData[]>([]);

  // ── Fetch Fear & Greed ──────────────────────────────────────────────────────
  useEffect(() => {
    let mounted = true;
    const fetchFNG = async () => {
      try {
        const res = await fetch("https://api.alternative.me/fng/?limit=1");
        const json = await res.json();
        if (mounted && json?.data?.[0]) {
          setFearGreedScore(parseInt(json.data[0].value));
        }
      } catch {
        // silently fall back to 50
      }
    };
    fetchFNG();
    const id = setInterval(fetchFNG, 3_600_000);
    return () => { mounted = false; clearInterval(id); };
  }, []);

  // ── Fetch historical klines on symbol change ──────────────────────────────
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchHistoricalKlines(chartSymbol, "1h", 200)
      .then((data) => {
        if (!cancelled) {
          candlesRef.current = data;
          setCandles(data);
        }
      })
      .catch(console.error)
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [chartSymbol]);

  // ── Merge latest live candle ──────────────────────────────────────────────
  useEffect(() => {
    if (!latestCandle || candlesRef.current.length === 0) return;
    const updated = [...candlesRef.current];
    const last = updated[updated.length - 1];
    if (last && latestCandle.time === last.time) {
      updated[updated.length - 1] = latestCandle;
    } else {
      updated.push(latestCandle);
    }
    candlesRef.current = updated;
    setCandles([...updated]);
  }, [latestCandle]);

  // ── Run AI modules ─────────────────────────────────────────────────────────
  const runAI = useCallback((data: CandleData[]) => {
    if (data.length < 5) return;

    // 1. Patterns
    const p = detectPatterns(data);
    setPatterns(p);

    // 2. Trend
    const t = analyzeTrend(data);
    setTrend(t);

    // 3. Volatility
    const v = scanVolatility(data);
    setVolatility(v);

    // 4. RSI for sentiment
    const rsiArr = calculateRSI(data, 14);
    const lastRsi = [...rsiArr].reverse().find((v) => v !== null) ?? null;

    // 5. Sentiment
    const whaleCount = toasts.filter((t) => t.type === "whale").length;
    const rektCount = toasts.filter((t) => t.type === "rekt").length;
    const input: SentimentInput = {
      fearGreedScore,
      rsiValue: lastRsi as number | null,
      trendDirection: t.direction,
      whaleCount,
      rektCount,
    };
    const s = calculateSentiment(input);
    setSentiment(s);
  }, [fearGreedScore, toasts]);

  useEffect(() => {
    if (!loading) runAI(candles);
  }, [candles, loading, runAI]);

  // ─── Render ─────────────────────────────────────────────────────────────────
  return (
    <div
      className="min-h-screen p-4 md:p-6 space-y-4"
      style={{ background: "#05050A" }}
    >
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -16 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="font-orbitron text-xl font-black tracking-widest text-[#00F0FF]"
            style={{ textShadow: "0 0 20px #00F0FF55" }}>
            AI INTELLIGENCE ENGINE
          </h1>
          <p className="font-mono text-[9px] text-white/30 mt-0.5 tracking-widest">
            AUTONOMOUS MARKET ANALYSIS • {chartSymbol} • LIVE
          </p>
        </div>
        <div className="flex items-center gap-2">
          <motion.div
            animate={{ opacity: [1, 0.4, 1] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="w-1.5 h-1.5 rounded-full bg-[#00FF66]"
          />
          <span className="font-mono text-[9px] text-[#00FF66]">LIVE</span>
        </div>
      </motion.div>

      {/* Row 1: Market Summary (full width) */}
      <AIMarketSummary sentiment={sentiment} trend={trend} loading={loading} />

      {/* Row 2: Pattern + Volatility + Trend */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <PatternDetector patterns={patterns} loading={loading} />
        <VolatilityScanner volatility={volatility} loading={loading} />
        <TrendCompass trend={trend} loading={loading} />
      </div>

      {/* Row 3: Correlation + Whale */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <CorrelationMatrix tickers={tickers} />
        <WhaleIntelligence whaleAlerts={whaleAlerts} toasts={toasts} />
      </div>

      {/* Row 4: AI Debate */}
      <div className="w-full">
        <AIDebate fearGreed={fearGreedScore} />
      </div>

      {/* Row 5: Monte Carlo Predictor */}
      <div className="w-full">
        <MonteCarloPredictor />
      </div>

      {/* Scan lines overlay */}
      <div
        className="pointer-events-none fixed inset-0 z-0 opacity-[0.025]"
        style={{
          backgroundImage:
            "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,240,255,0.5) 2px, rgba(0,240,255,0.5) 3px)",
          backgroundSize: "100% 3px",
        }}
      />
    </div>
  );
}
