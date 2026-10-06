"use client";

import React, { useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAutonomousTrader } from "../../lib/hooks/useAutonomousTrader";
import DailyDrawdownGuard from "../../components/dom/DailyDrawdownGuard";

export default function AutonomousPage() {
  const {
    state,
    config,
    start,
    stop,
    updateConfig,
    isRunning,
    currentSignal,
    wallets,
    logs,
    evaluationCount,
  } = useAutonomousTrader();

  const recentLogs = useMemo(() => logs.slice(0, 50), [logs]);

  const signalColor = currentSignal
    ? currentSignal.score > 65
      ? "#00FF66"
      : currentSignal.score < 35
      ? "#FF0055"
      : "#FFA500"
    : "#666";

  const directionEmoji = currentSignal
    ? { STRONG_BUY: "🚀", BUY: "📈", NEUTRAL: "➡️", SELL: "📉", STRONG_SELL: "💥" }[currentSignal.direction] || "❓"
    : "⏸";

  return (
    <div className="min-h-screen">
      <DailyDrawdownGuard maxDailyDrawdownPct={5} />

      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div>
            <h1 className="font-orbitron font-black text-2xl tracking-wider" style={{ color: isRunning ? "#00F0FF" : "#666" }}>
              AUTONOMOUS TRADER
            </h1>
            <p className="font-mono text-[10px] text-[rgba(255,255,255,0.4)] mt-1">
              Graph Engine → Paper Wallets → AI Training → Self-Optimization
            </p>
          </div>

          {/* Master Toggle */}
          <button
            onClick={isRunning ? stop : start}
            className="font-orbitron text-sm tracking-wider px-8 py-3 rounded-xl font-bold transition-all duration-500"
            style={{
              background: isRunning
                ? "linear-gradient(135deg, #FF0055, #990033)"
                : "linear-gradient(135deg, #00FF66, #009933)",
              color: "white",
              boxShadow: isRunning
                ? "0 0 30px rgba(255,0,85,0.4)"
                : "0 0 30px rgba(0,255,102,0.4)",
            }}
          >
            {isRunning ? "⏹ STOP ENGINE" : "▶ START ENGINE"}
          </button>
        </div>

        {/* Signal Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Unified Signal */}
          <div className="md:col-span-2 border rounded-2xl p-6 backdrop-blur-md relative overflow-hidden"
            style={{ borderColor: `${signalColor}33`, backgroundColor: `${signalColor}08` }}>
            <div className="absolute inset-0 opacity-10" style={{ background: `radial-gradient(ellipse at center, ${signalColor}22, transparent)` }} />
            <div className="relative z-10 text-center">
              <span className="font-mono text-[9px] text-[rgba(255,255,255,0.4)]">UNIFIED SIGNAL SCORE</span>
              <div className="flex items-center justify-center gap-4 mt-2">
                <span className="text-4xl">{directionEmoji}</span>
                <span className="font-orbitron text-5xl font-black" style={{ color: signalColor }}>
                  {currentSignal ? currentSignal.score.toFixed(0) : "--"}
                </span>
                <span className="font-orbitron text-lg" style={{ color: signalColor }}>
                  {currentSignal?.direction ?? "OFFLINE"}
                </span>
              </div>
              <div className="mt-3 flex justify-center gap-6">
                <div>
                  <span className="font-mono text-[8px] text-[rgba(255,255,255,0.4)] block">CONFIDENCE</span>
                  <span className="font-mono text-sm font-bold text-white">
                    {currentSignal ? `${(currentSignal.confidence * 100).toFixed(0)}%` : "--"}
                  </span>
                </div>
                <div>
                  <span className="font-mono text-[8px] text-[rgba(255,255,255,0.4)] block">EVALUATIONS</span>
                  <span className="font-mono text-sm font-bold text-[#00F0FF]">{evaluationCount}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Top Signals */}
          <div className="md:col-span-2 border border-[rgba(139,0,255,0.2)] rounded-2xl p-5 bg-[rgba(139,0,255,0.03)]">
            <h3 className="font-orbitron text-xs text-[#8B00FF] tracking-wider mb-3">TOP CONTRIBUTING SIGNALS</h3>
            <div className="space-y-2">
              {(currentSignal?.topSignals ?? []).slice(0, 5).map((sig, i) => (
                <div key={sig.nodeId} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[10px] text-[rgba(255,255,255,0.3)] w-3">{i + 1}</span>
                    <span className="font-mono text-[10px] text-white">{sig.name}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-20 h-1 bg-[rgba(255,255,255,0.05)] rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${Math.abs(sig.contribution) * 100}%`,
                          backgroundColor: sig.contribution > 0 ? "#00FF66" : "#FF0055",
                        }}
                      />
                    </div>
                    <span className={`font-mono text-[10px] font-bold ${sig.value > 0 ? "text-[#00FF66]" : "text-[#FF0055]"}`}>
                      {sig.value > 0 ? "+" : ""}{(sig.value * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
              {(!currentSignal?.topSignals || currentSignal.topSignals.length === 0) && (
                <span className="font-mono text-[10px] text-[rgba(255,255,255,0.2)]">Engine not running</span>
              )}
            </div>
          </div>
        </div>

        {/* Config Panel */}
        <div className="border border-[rgba(255,255,255,0.08)] rounded-xl p-5 bg-[rgba(10,10,20,0.4)]">
          <h3 className="font-orbitron text-xs text-[rgba(255,255,255,0.5)] tracking-wider mb-4">ENGINE CONFIGURATION</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <ConfigInput label="Eval Interval (sec)" value={config.evaluationIntervalMs / 1000} onChange={(v) => updateConfig({ evaluationIntervalMs: v * 1000 })} />
            <ConfigInput label="Min Confidence" value={config.minConfidence} onChange={(v) => updateConfig({ minConfidence: v })} step={0.05} />
            <ConfigInput label="Min Score Deviation" value={config.minSignalScore} onChange={(v) => updateConfig({ minSignalScore: v })} />
            <ConfigInput label="Max Position %" value={config.maxPositionPct * 100} onChange={(v) => updateConfig({ maxPositionPct: v / 100 })} />
          </div>
        </div>

        {/* Wallets Status */}
        <div className="border border-[rgba(0,240,255,0.15)] rounded-xl p-5 bg-[rgba(0,240,255,0.02)]">
          <h3 className="font-orbitron text-xs text-[#00F0FF] tracking-wider mb-4">PAPER WALLETS</h3>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            {wallets.map((w) => {
              const pnl = w.currentCapital - w.initialCapital;
              return (
                <div key={w.id} className="border border-[rgba(255,255,255,0.08)] rounded-lg p-3 bg-[rgba(0,0,0,0.3)]">
                  <span className="font-mono text-[8px] text-[rgba(255,255,255,0.4)] block truncate">{w.name}</span>
                  <span className="font-orbitron text-sm font-bold text-white block mt-1">
                    ${w.currentCapital.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </span>
                  <div className="flex justify-between mt-1">
                    <span className={`font-mono text-[9px] font-bold ${pnl >= 0 ? "text-[#00FF66]" : "text-[#FF0055]"}`}>
                      {pnl >= 0 ? "+" : ""}{((pnl / w.initialCapital) * 100).toFixed(2)}%
                    </span>
                    <span className="font-mono text-[8px] text-[rgba(255,255,255,0.3)]">{w.stats.totalTrades} trades</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Live Logs */}
        <div className="border border-[rgba(255,255,255,0.08)] rounded-xl p-5 bg-[rgba(5,5,15,0.6)]">
          <h3 className="font-orbitron text-xs text-[rgba(255,255,255,0.5)] tracking-wider mb-3">EXECUTION LOG</h3>
          <div className="h-64 overflow-y-auto space-y-1 font-mono text-[10px]" style={{ scrollbarWidth: "thin" }}>
            <AnimatePresence initial={false}>
              {recentLogs.map((log, i) => {
                const typeColor = {
                  evaluation: "#00F0FF",
                  trade: "#00FF66",
                  training: "#8B00FF",
                  error: "#FF0055",
                  info: "#FFA500",
                }[log.type] || "#666";

                return (
                  <motion.div
                    key={`${log.timestamp}-${i}`}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="flex gap-2 py-0.5"
                  >
                    <span className="text-[rgba(255,255,255,0.2)] shrink-0">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                    <span className="shrink-0 w-10" style={{ color: typeColor }}>
                      [{log.type.slice(0, 4).toUpperCase()}]
                    </span>
                    <span className="text-[rgba(255,255,255,0.7)]">{log.message}</span>
                  </motion.div>
                );
              })}
            </AnimatePresence>
            {recentLogs.length === 0 && (
              <span className="text-[rgba(255,255,255,0.2)]">Start the engine to see logs...</span>
            )}
          </div>
        </div>

        {/* Reasoning */}
        {currentSignal?.reasoning && (
          <div className="border border-[rgba(0,255,102,0.15)] rounded-xl p-5 bg-[rgba(0,255,102,0.02)]">
            <h3 className="font-orbitron text-xs text-[#00FF66] tracking-wider mb-2">AI REASONING</h3>
            <p className="font-mono text-[11px] text-[rgba(255,255,255,0.6)] leading-relaxed">
              {currentSignal.reasoning}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function ConfigInput({
  label,
  value,
  onChange,
  step = 1,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  step?: number;
}) {
  return (
    <div>
      <label className="font-mono text-[8px] text-[rgba(255,255,255,0.3)] block mb-1">{label}</label>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        step={step}
        className="w-full bg-[rgba(0,0,0,0.4)] border border-[rgba(255,255,255,0.1)] rounded px-2 py-1.5 text-white font-mono text-xs focus:border-[#00F0FF] focus:outline-none"
      />
    </div>
  );
}
