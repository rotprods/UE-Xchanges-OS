"use client";

import React, { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface PaperWallet {
  id: string;
  name: string;
  strategyId: string;
  initialCapital: number;
  currentCapital: number;
  totalTrades: number;
  winCount: number;
  lossCount: number;
  winRate: number;
  sharpeRatio: number;
  maxDrawdown: number;
  totalReturn: number;
  profitFactor: number;
  consecutiveLosses: number;
  maxConsecutiveLosses: number;
  equityCurve: number[];
  status: string;
  createdAt: number;
}

interface GraduationResult {
  passed: boolean;
  criteriaResults: { criterion: string; required: number; actual: number; passed: boolean }[];
  readinessScore: number;
  recommendation: string;
}

const STATUS_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  training: { bg: "rgba(0,240,255,0.08)", border: "rgba(0,240,255,0.3)", text: "#00F0FF" },
  evaluating: { bg: "rgba(255,165,0,0.08)", border: "rgba(255,165,0,0.3)", text: "#FFA500" },
  graduated: { bg: "rgba(0,255,102,0.08)", border: "rgba(0,255,102,0.3)", text: "#00FF66" },
  live_sandbox: { bg: "rgba(139,0,255,0.08)", border: "rgba(139,0,255,0.3)", text: "#8B00FF" },
  live_real: { bg: "rgba(255,215,0,0.08)", border: "rgba(255,215,0,0.3)", text: "#FFD700" },
  suspended: { bg: "rgba(255,0,85,0.08)", border: "rgba(255,0,85,0.3)", text: "#FF0055" },
};

const STRATEGY_ICONS: Record<string, string> = {
  sma_crossover: "📈",
  rsi_reversion: "🔄",
  breakout_momentum: "🚀",
  bb_squeeze: "🎯",
  ensemble_graph: "🧠",
};

export default function WalletsPage() {
  const [wallets, setWallets] = useState<PaperWallet[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedWallet, setSelectedWallet] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [newStrategy, setNewStrategy] = useState("sma_crossover");

  const fetchWallets = useCallback(async () => {
    try {
      const res = await fetch("/api/wallets");
      if (!res.ok) return;
      const data = await res.json();
      setWallets(data.wallets || []);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWallets();
    const interval = setInterval(fetchWallets, 10000);
    return () => clearInterval(interval);
  }, [fetchWallets]);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    try {
      const res = await fetch("/api/wallets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newName, strategyId: newStrategy }),
      });
      if (res.ok) {
        setCreating(false);
        setNewName("");
        fetchWallets();
      }
    } catch {
      // silent
    }
  };

  const totalCapital = wallets.reduce((s, w) => s + w.currentCapital, 0);
  const avgWinRate = wallets.length > 0
    ? wallets.reduce((s, w) => s + w.winRate, 0) / wallets.length
    : 0;
  const totalTrades = wallets.reduce((s, w) => s + w.totalTrades, 0);
  const bestWallet = wallets.length > 0
    ? wallets.reduce((best, w) => w.totalReturn > best.totalReturn ? w : best)
    : null;

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="font-orbitron font-black text-2xl text-[#00F0FF] tracking-wider">
            PAPER WALLET LABORATORY
          </h1>
          <p className="font-mono text-[10px] text-[rgba(255,255,255,0.4)] mt-1">
            AI-driven autonomous traders training on real market data
          </p>
        </div>
        <button
          onClick={() => setCreating(true)}
          className="font-orbitron text-[10px] tracking-wider px-4 py-2 rounded-lg border border-[rgba(0,240,255,0.4)] bg-[rgba(0,240,255,0.1)] text-[#00F0FF] hover:bg-[rgba(0,240,255,0.2)] transition-all"
        >
          + NEW WALLET
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="TOTAL CAPITAL" value={`$${totalCapital.toLocaleString(undefined, { maximumFractionDigits: 0 })}`} color="#00F0FF" />
        <StatCard label="ACTIVE WALLETS" value={wallets.length.toString()} color="#8B00FF" />
        <StatCard label="TOTAL TRADES" value={totalTrades.toString()} color="#FF5500" />
        <StatCard label="AVG WIN RATE" value={`${(avgWinRate * 100).toFixed(1)}%`} color={avgWinRate >= 0.55 ? "#00FF66" : "#FF0055"} />
      </div>

      {/* Create Wallet Modal */}
      <AnimatePresence>
        {creating && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="border border-[rgba(0,240,255,0.3)] bg-[rgba(5,10,20,0.8)] backdrop-blur-md rounded-xl p-6"
          >
            <h3 className="font-orbitron text-sm text-[#00F0FF] tracking-wider mb-4">CREATE NEW PAPER WALLET</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="font-mono text-[9px] text-[rgba(255,255,255,0.4)] block mb-1">WALLET NAME</label>
                <input
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="e.g. Zeta — Custom Strategy"
                  className="w-full bg-[rgba(0,0,0,0.4)] border border-[rgba(255,255,255,0.1)] rounded px-3 py-2 text-white font-mono text-xs focus:border-[#00F0FF] focus:outline-none"
                />
              </div>
              <div>
                <label className="font-mono text-[9px] text-[rgba(255,255,255,0.4)] block mb-1">STRATEGY</label>
                <select
                  value={newStrategy}
                  onChange={(e) => setNewStrategy(e.target.value)}
                  className="w-full bg-[rgba(0,0,0,0.4)] border border-[rgba(255,255,255,0.1)] rounded px-3 py-2 text-white font-mono text-xs focus:border-[#00F0FF] focus:outline-none"
                >
                  <option value="sma_crossover">📈 SMA Crossover</option>
                  <option value="rsi_reversion">🔄 RSI Mean Reversion</option>
                  <option value="breakout_momentum">🚀 Breakout Momentum</option>
                  <option value="bb_squeeze">🎯 BB Squeeze</option>
                  <option value="ensemble_graph">🧠 Ensemble (Graph Engine)</option>
                </select>
              </div>
              <div className="flex items-end gap-2">
                <button
                  onClick={handleCreate}
                  className="flex-1 font-orbitron text-[10px] px-4 py-2 rounded-lg bg-[#00F0FF] text-black font-bold hover:bg-[#00D4E0] transition-all"
                >
                  DEPLOY WALLET
                </button>
                <button
                  onClick={() => setCreating(false)}
                  className="font-mono text-[10px] px-3 py-2 rounded-lg border border-[rgba(255,255,255,0.1)] text-[rgba(255,255,255,0.4)] hover:text-white transition-all"
                >
                  CANCEL
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Wallet Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-8 h-8 border-2 border-t-transparent border-[#00F0FF] rounded-full animate-spin" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {wallets.map((wallet, i) => (
            <WalletCard
              key={wallet.id}
              wallet={wallet}
              index={i}
              isSelected={selectedWallet === wallet.id}
              onSelect={() => setSelectedWallet(selectedWallet === wallet.id ? null : wallet.id)}
            />
          ))}
        </div>
      )}

      {/* Graduation Criteria Reference */}
      <div className="border border-[rgba(0,255,102,0.2)] bg-[rgba(0,255,102,0.03)] rounded-xl p-5">
        <h3 className="font-orbitron text-xs text-[#00FF66] tracking-wider mb-3">GRADUATION CRITERIA</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { name: "Win Rate", value: "≥ 55%" },
            { name: "Sharpe Ratio", value: "≥ 1.5" },
            { name: "Max Drawdown", value: "≤ 15%" },
            { name: "Total Return", value: "≥ 10%" },
            { name: "Profit Factor", value: "≥ 1.8" },
            { name: "Max Consec. Losses", value: "≤ 5" },
            { name: "Min Trades", value: "≥ 100" },
            { name: "Min Days Active", value: "≥ 30" },
          ].map((c) => (
            <div key={c.name} className="flex justify-between items-center font-mono text-[10px] border-b border-[rgba(255,255,255,0.05)] pb-1">
              <span className="text-[rgba(255,255,255,0.5)]">{c.name}</span>
              <span className="text-[#00FF66] font-bold">{c.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function WalletCard({
  wallet,
  index,
  isSelected,
  onSelect,
}: {
  wallet: PaperWallet;
  index: number;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const colors = STATUS_COLORS[wallet.status] || STATUS_COLORS.training;
  const icon = STRATEGY_ICONS[wallet.strategyId] || "📊";
  const pnl = wallet.currentCapital - wallet.initialCapital;
  const pnlPct = wallet.totalReturn;

  // Mini equity curve SVG
  const curve = wallet.equityCurve;
  const curveMin = Math.min(...curve);
  const curveMax = Math.max(...curve);
  const curveRange = curveMax - curveMin || 1;
  const curvePoints = curve
    .map((v, i) => {
      const x = (i / (curve.length - 1 || 1)) * 100;
      const y = 100 - ((v - curveMin) / curveRange) * 100;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.05 }}
      onClick={onSelect}
      className="cursor-pointer border rounded-xl p-5 relative overflow-hidden transition-all duration-300 hover:shadow-[0_0_20px_rgba(0,240,255,0.1)]"
      style={{
        backgroundColor: colors.bg,
        borderColor: isSelected ? colors.text : colors.border,
        boxShadow: isSelected ? `0 0 25px ${colors.bg}` : undefined,
      }}
    >
      {/* Background gradient */}
      <div
        className="absolute inset-0 opacity-20 pointer-events-none"
        style={{ background: `radial-gradient(ellipse at bottom right, ${colors.text}22, transparent)` }}
      />

      {/* Header */}
      <div className="flex justify-between items-start mb-3 relative z-10">
        <div className="flex items-center gap-2">
          <span className="text-xl">{icon}</span>
          <div>
            <h3 className="font-orbitron text-xs font-bold text-white tracking-wide">{wallet.name}</h3>
            <span className="font-mono text-[8px] text-[rgba(255,255,255,0.4)]">{wallet.strategyId.replace(/_/g, " ").toUpperCase()}</span>
          </div>
        </div>
        <span
          className="font-mono text-[8px] tracking-wider px-2 py-0.5 rounded-full border font-bold"
          style={{ color: colors.text, borderColor: colors.border, backgroundColor: `${colors.text}15` }}
        >
          {wallet.status.toUpperCase().replace("_", " ")}
        </span>
      </div>

      {/* P&L */}
      <div className="mb-3 relative z-10">
        <span className="block font-mono text-[9px] text-[rgba(255,255,255,0.4)]">CAPITAL / P&L</span>
        <div className="flex items-baseline gap-3">
          <span className="font-orbitron text-lg font-bold text-white">
            ${wallet.currentCapital.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </span>
          <span className={`font-mono text-xs font-bold ${pnl >= 0 ? "text-[#00FF66]" : "text-[#FF0055]"}`}>
            {pnl >= 0 ? "+" : ""}{pnlPct.toFixed(2)}%
          </span>
        </div>
      </div>

      {/* Mini Equity Curve */}
      {curve.length > 1 && (
        <div className="mb-3 relative z-10">
          <svg viewBox="0 0 100 40" className="w-full h-10" preserveAspectRatio="none">
            <polyline
              points={curvePoints}
              fill="none"
              stroke={pnl >= 0 ? "#00FF66" : "#FF0055"}
              strokeWidth="1.5"
              vectorEffect="non-scaling-stroke"
              opacity={0.7}
            />
          </svg>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-3 gap-2 relative z-10">
        <MiniStat label="TRADES" value={wallet.totalTrades.toString()} />
        <MiniStat label="WIN RATE" value={`${(wallet.winRate * 100).toFixed(1)}%`} color={wallet.winRate >= 0.55 ? "#00FF66" : undefined} />
        <MiniStat label="SHARPE" value={wallet.sharpeRatio.toFixed(2)} color={wallet.sharpeRatio >= 1.5 ? "#00FF66" : undefined} />
        <MiniStat label="DRAWDOWN" value={`${(wallet.maxDrawdown * 100).toFixed(1)}%`} color={wallet.maxDrawdown <= 0.15 ? "#00FF66" : "#FF0055"} />
        <MiniStat label="P. FACTOR" value={wallet.profitFactor.toFixed(2)} />
        <MiniStat label="CONSEC. L" value={wallet.maxConsecutiveLosses.toString()} color={wallet.maxConsecutiveLosses <= 5 ? "#00FF66" : "#FF0055"} />
      </div>

      {/* Expanded Details */}
      <AnimatePresence>
        {isSelected && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-3 pt-3 border-t border-[rgba(255,255,255,0.1)] relative z-10"
          >
            <div className="grid grid-cols-2 gap-2">
              <MiniStat label="WINS" value={wallet.winCount.toString()} color="#00FF66" />
              <MiniStat label="LOSSES" value={wallet.lossCount.toString()} color="#FF0055" />
              <MiniStat label="INITIAL" value={`$${wallet.initialCapital.toLocaleString()}`} />
              <MiniStat label="CREATED" value={new Date(wallet.createdAt).toLocaleDateString()} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div
      className="border rounded-xl p-4 backdrop-blur-md relative overflow-hidden"
      style={{ borderColor: `${color}33`, backgroundColor: `${color}08` }}
    >
      <div className="absolute inset-0 opacity-10" style={{ background: `radial-gradient(ellipse at bottom, ${color}22, transparent)` }} />
      <span className="block font-mono text-[9px] tracking-wider relative z-10" style={{ color: `${color}99` }}>{label}</span>
      <span className="block font-orbitron text-lg font-bold mt-1 relative z-10" style={{ color }}>{value}</span>
    </div>
  );
}

function MiniStat({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="flex flex-col">
      <span className="font-mono text-[7px] text-[rgba(255,255,255,0.3)]">{label}</span>
      <span className={`font-mono text-[10px] font-bold ${color ? "" : "text-white"}`} style={color ? { color } : undefined}>{value}</span>
    </div>
  );
}
