"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { fetchHistoricalKlines } from "../../lib/api/binanceRest";
import { runBacktest, smaCrossoverStrategy, rsiStrategy, BacktestResult } from "../../lib/backtest";

const SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT"];
const INTERVALS = ["15m", "1h", "4h", "1d"];
const STRATEGIES = [
  { id: "sma", label: "SMA Crossover (7/25)" },
  { id: "rsi", label: "RSI Strategy (30/70)" },
];

function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div
      className="rounded-xl p-4 border backdrop-blur-md relative overflow-hidden"
      style={{ borderColor: `${color}33`, backgroundColor: `${color}0A` }}
    >
      <span className="block font-mono text-[9px] tracking-wider" style={{ color: `${color}88` }}>{label}</span>
      <span className="block font-orbitron text-xl font-bold mt-1" style={{ color }}>{value}</span>
    </div>
  );
}

function EquityCurve({ curve, initialCapital }: { curve: number[]; initialCapital: number }) {
  if (curve.length < 2) return null;
  const min = Math.min(...curve);
  const max = Math.max(...curve);
  const range = max - min || 1;
  const width = 600;
  const height = 120;
  const isProfitable = curve[curve.length - 1] >= initialCapital;

  const points = curve.map((v, i) => {
    const x = (i / (curve.length - 1)) * width;
    const y = height - ((v - min) / range) * height;
    return `${x},${y}`;
  }).join(" ");

  return (
    <div className="w-full overflow-hidden rounded-lg border border-[rgba(255,255,255,0.05)]">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-[120px]" preserveAspectRatio="none">
        <defs>
          <linearGradient id="curveGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={isProfitable ? "#00FF66" : "#FF0055"} stopOpacity="0.4" />
            <stop offset="100%" stopColor={isProfitable ? "#00FF66" : "#FF0055"} stopOpacity="0" />
          </linearGradient>
        </defs>
        {/* Area fill */}
        <polygon
          points={`0,${height} ${points} ${width},${height}`}
          fill="url(#curveGrad)"
        />
        {/* Line */}
        <polyline
          points={points}
          fill="none"
          stroke={isProfitable ? "#00FF66" : "#FF0055"}
          strokeWidth="2"
          strokeLinejoin="round"
        />
        {/* Baseline */}
        <line
          x1="0" y1={height - ((initialCapital - min) / range) * height}
          x2={width} y2={height - ((initialCapital - min) / range) * height}
          stroke="rgba(255,255,255,0.1)" strokeWidth="1" strokeDasharray="4,4"
        />
      </svg>
    </div>
  );
}

export default function BacktestPanel() {
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [interval, setInterval] = useState("1h");
  const [strategyId, setStrategyId] = useState("sma");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runTest = async () => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      const candles = await fetchHistoricalKlines(symbol, interval, 500);
      const strategy = strategyId === "sma" ? smaCrossoverStrategy : rsiStrategy;
      const res = runBacktest(candles, strategy, 100000);
      setResult(res);
    } catch (e: any) {
      setError(e.message || "Backtest failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="border border-[rgba(0,240,255,0.3)] bg-[rgba(5,15,25,0.4)] backdrop-blur-md rounded-2xl p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-orbitron font-bold text-[#00F0FF] text-sm tracking-widest flex items-center">
          <span className="w-1.5 h-1.5 bg-[#00F0FF] rounded-full mr-2 animate-pulse" />
          STRATEGY BACKTESTER
        </h3>
        <span className="font-mono text-[9px] text-[rgba(255,255,255,0.3)]">HISTORICAL SIMULATION ENGINE</span>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap gap-4 items-end">
        <div>
          <span className="block font-mono text-[9px] text-[rgba(255,255,255,0.4)] mb-1">ASSET</span>
          <select
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            className="bg-[rgba(0,240,255,0.05)] border border-[rgba(0,240,255,0.3)] text-[#00F0FF] font-mono text-xs px-3 py-2 rounded-lg outline-none"
          >
            {SYMBOLS.map((s) => <option key={s} value={s} className="bg-[#0A0A14]">{s.replace("USDT", "")}</option>)}
          </select>
        </div>
        <div>
          <span className="block font-mono text-[9px] text-[rgba(255,255,255,0.4)] mb-1">TIMEFRAME</span>
          <div className="flex overflow-hidden rounded-lg border border-[rgba(255,255,255,0.1)]">
            {INTERVALS.map((int) => (
              <button
                key={int}
                onClick={() => setInterval(int)}
                className={`px-3 py-2 text-[10px] font-mono transition-all ${interval === int ? "bg-[rgba(0,240,255,0.15)] text-[#00F0FF]" : "text-[rgba(255,255,255,0.4)]"}`}
              >
                {int}
              </button>
            ))}
          </div>
        </div>
        <div>
          <span className="block font-mono text-[9px] text-[rgba(255,255,255,0.4)] mb-1">STRATEGY</span>
          <select
            value={strategyId}
            onChange={(e) => setStrategyId(e.target.value)}
            className="bg-[rgba(0,240,255,0.05)] border border-[rgba(0,240,255,0.3)] text-[#00F0FF] font-mono text-xs px-3 py-2 rounded-lg outline-none"
          >
            {STRATEGIES.map((s) => <option key={s.id} value={s.id} className="bg-[#0A0A14]">{s.label}</option>)}
          </select>
        </div>
        <button
          onClick={runTest}
          disabled={isLoading}
          className="px-6 py-2 bg-[rgba(0,240,255,0.1)] border border-[#00F0FF] text-[#00F0FF] font-orbitron font-bold text-xs rounded-lg hover:bg-[rgba(0,240,255,0.2)] hover:shadow-[0_0_15px_rgba(0,240,255,0.3)] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? "COMPUTING..." : "▶ RUN BACKTEST"}
        </button>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-8 space-x-3">
          <div className="w-6 h-6 border-2 border-t-transparent border-[#00F0FF] rounded-full animate-spin" />
          <span className="font-mono text-[10px] text-[rgba(255,255,255,0.5)]">FETCHING HISTORICAL DATA & SIMULATING...</span>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="border border-[rgba(255,0,85,0.4)] bg-[rgba(255,0,85,0.1)] rounded-lg p-3 font-mono text-[10px] text-[#FF0055]">
          ⚠ {error}
        </div>
      )}

      {/* Results */}
      <AnimatePresence>
        {result && !isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="space-y-4"
          >
            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <StatCard
                label="TOTAL RETURN"
                value={`${result.totalReturn >= 0 ? "+" : ""}${result.totalReturn.toFixed(2)}%`}
                color={result.totalReturn >= 0 ? "#00FF66" : "#FF0055"}
              />
              <StatCard label="WIN RATE" value={`${result.winRate.toFixed(1)}%`} color="#00F0FF" />
              <StatCard label="MAX DRAWDOWN" value={`-${result.maxDrawdown.toFixed(2)}%`} color="#FF5500" />
              <StatCard label="SHARPE RATIO" value={result.sharpeRatio.toFixed(2)} color="#8B00FF" />
            </div>

            {/* Summary row */}
            <div className="flex justify-between font-mono text-[10px] text-[rgba(255,255,255,0.5)]">
              <span>Initial: <span className="text-white">${result.initialCapital.toLocaleString()}</span></span>
              <span>Final: <span className={result.finalCapital >= result.initialCapital ? "text-[#00FF66]" : "text-[#FF0055]"}>${result.finalCapital.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}</span></span>
              <span>Trades: <span className="text-white">{result.trades.length}</span></span>
              <span>Winning: <span className="text-[#00FF66]">{result.trades.filter((t) => t.pnl > 0).length}</span></span>
            </div>

            {/* Equity Curve */}
            <div>
              <h4 className="font-mono text-[9px] text-[rgba(255,255,255,0.4)] mb-2">EQUITY CURVE</h4>
              <EquityCurve curve={result.equityCurve} initialCapital={result.initialCapital} />
            </div>

            {/* Trade List */}
            {result.trades.length > 0 && (
              <div>
                <h4 className="font-mono text-[9px] text-[rgba(255,255,255,0.4)] mb-2">LAST TRADES</h4>
                <div className="space-y-1 max-h-[200px] overflow-y-auto">
                  {result.trades.slice(-10).reverse().map((trade, i) => (
                    <div key={i} className="flex justify-between items-center font-mono text-[10px] border-b border-[rgba(255,255,255,0.05)] pb-1">
                      <span className="text-[rgba(255,255,255,0.5)]">Entry: <span className="text-white">${trade.entryPrice.toFixed(2)}</span></span>
                      <span className="text-[rgba(255,255,255,0.5)]">Exit: <span className="text-white">${trade.exitPrice.toFixed(2)}</span></span>
                      <span className={trade.pnl >= 0 ? "text-[#00FF66] font-bold" : "text-[#FF0055] font-bold"}>
                        {trade.pnl >= 0 ? "+" : ""}{trade.pnlPct.toFixed(2)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
