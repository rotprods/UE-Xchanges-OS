"use client";

import React, { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { useOmniStore } from "../../store/omniStore";

function formatTVL(value: number): string {
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  return `$${value.toLocaleString()}`;
}

export default function DefiPanel() {
  const defiTVL = useOmniStore((state) => state.defiTVL);
  const { total, change24h, chains } = defiTVL;

  const isPositive = change24h >= 0;
  const changeColor = isPositive ? "#00FF66" : "#FF0055";
  const maxChainTvl = chains.length > 0 ? Math.max(...chains.map((c) => c.tvl)) : 1;

  // Animate bar widths on mount / update
  const barRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    barRefs.current.forEach((el, i) => {
      if (!el) return;
      const chain = chains[i];
      if (!chain) return;
      const pct = maxChainTvl > 0 ? (chain.tvl / maxChainTvl) * 100 : 0;
      // Trigger via requestAnimationFrame so CSS transition fires
      el.style.width = "0%";
      const raf = requestAnimationFrame(() => {
        el.style.width = `${pct}%`;
      });
      return () => cancelAnimationFrame(raf);
    });
  }, [chains, maxChainTvl]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="border border-[rgba(0,240,255,0.3)] bg-[rgba(5,15,25,0.4)] backdrop-blur-md rounded-2xl p-4 space-y-4"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <h4 className="font-orbitron text-[9px] tracking-widest text-[#00F0FF] flex items-center gap-2">
          <span className="w-1.5 h-1.5 bg-[#00F0FF] rounded-full animate-pulse" />
          DEFI TVL
        </h4>
        {total === 0 && (
          <span className="font-mono text-[9px] text-[rgba(255,255,255,0.3)] animate-pulse">
            SYNCING...
          </span>
        )}
      </div>

      {/* Total TVL */}
      <div className="flex items-end gap-3">
        <span className="font-orbitron text-2xl font-black text-white tracking-tight">
          {total > 0 ? formatTVL(total) : "—"}
        </span>
        {total > 0 && (
          <span
            className="font-mono text-xs font-bold mb-0.5"
            style={{ color: changeColor }}
          >
            {isPositive ? "▲" : "▼"} {Math.abs(change24h).toFixed(2)}% 24h
          </span>
        )}
      </div>

      {/* Top Chains */}
      {chains.length > 0 && (
        <div className="space-y-2">
          <span className="font-mono text-[9px] text-[rgba(255,255,255,0.35)] tracking-widest">
            TOP CHAINS
          </span>
          {chains.map((chain, i) => {
            const chainChange = chain.change24h ?? 0;
            const chainPos = chainChange >= 0;
            const chainColor = chainPos ? "#00FF66" : "#FF0055";

            return (
              <div key={chain.name} className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-orbitron text-[10px] font-bold text-white">
                    {chain.name}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[9px] text-[rgba(255,255,255,0.5)]">
                      {formatTVL(chain.tvl)}
                    </span>
                    <span
                      className="font-mono text-[9px] font-bold"
                      style={{ color: chainColor }}
                    >
                      {chainPos ? "+" : ""}{chainChange.toFixed(2)}%
                    </span>
                  </div>
                </div>
                {/* Bar */}
                <div className="w-full h-1.5 bg-[rgba(255,255,255,0.06)] rounded-full overflow-hidden">
                  <div
                    ref={(el) => { barRefs.current[i] = el; }}
                    className="h-full rounded-full"
                    style={{
                      width: "0%",
                      background: `linear-gradient(90deg, #00F0FF, #8B00FF)`,
                      transition: "width 1.2s cubic-bezier(0.16, 1, 0.3, 1)",
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {chains.length === 0 && total === 0 && (
        <div className="text-center py-4">
          <p className="font-mono text-[10px] text-[rgba(255,255,255,0.2)]">
            FETCHING CHAIN DATA...
          </p>
        </div>
      )}
    </motion.div>
  );
}
