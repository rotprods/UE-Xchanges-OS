"use client";

import React, { useState } from "react";
import { useOmniStore } from "../../store/omniStore";

/** Deterministic number formatter — no locale dependency (avoids SSR/CSR hydration mismatch). */
function formatNumber(value: number, decimals: number = 0): string {
  const fixed = value.toFixed(decimals);
  const [integer, fraction] = fixed.split(".");
  const withCommas = integer.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return fraction !== undefined ? `${withCommas}.${fraction}` : withCommas;
}

export default function TradingPanel() {
  const portfolio = useOmniStore((state) => state.portfolio);
  const executeTrade = useOmniStore((state) => state.executeTrade);
  const chartSymbol = useOmniStore((state) => state.chartSymbol);
  const latestCandle = useOmniStore((state) => state.latestCandle);
  
  const [amountUsd, setAmountUsd] = useState<number | string>(10000);
  const [flash, setFlash] = useState<"BUY" | "SELL" | null>(null);

  const handleTrade = (side: "BUY" | "SELL") => {
    const amt = typeof amountUsd === "string" ? parseFloat(amountUsd) : amountUsd;
    if (isNaN(amt) || amt <= 0 || !latestCandle) return;

    executeTrade(chartSymbol, side, amt, latestCandle.close);
    
    setFlash(side);
    setTimeout(() => setFlash(null), 300);
  };

  const currentPrice = latestCandle?.close || 0;
  const assetBalance = portfolio.assets[chartSymbol] || 0;
  const assetValueUsd = assetBalance * currentPrice;
  const totalValue = portfolio.usdt + Object.entries(portfolio.assets).reduce((acc, [sym, qty]) => {
    // We only have the precise price of the currently selected symbol easily available here,
    // so total value might be approximate if they hold other things. 
    // For MVP, we'll just show the exact USDT + current symbol value for simplicity.
    return acc + (sym === chartSymbol ? qty * currentPrice : 0); 
  }, 0);

  return (
    <div className={`glass-panel border p-5 rounded-2xl flex flex-col relative overflow-hidden transition-all duration-300 ${
      flash === "BUY" ? "border-[#00FF66] shadow-[0_0_30px_rgba(0,255,102,0.5)]" :
      flash === "SELL" ? "border-[#FF5500] shadow-[0_0_30px_rgba(255,85,0,0.5)]" :
      "border-[rgba(0,240,255,0.3)]"
    }`}>
      {/* Background Glitch on Flash */}
      {flash && <div className={`absolute inset-0 opacity-20 mix-blend-overlay ${flash === "BUY" ? "bg-[#00FF66]" : "bg-[#FF5500]"}`} />}

      <div className="flex justify-between items-center border-b border-[rgba(255,255,255,0.1)] pb-3 mb-4 z-10">
        <h3 className="font-orbitron font-bold text-[#00F0FF] tracking-wider text-sm flex items-center">
          QUANTUM CASINO <span className="ml-2 font-mono text-[9px] text-[rgba(255,255,255,0.4)]">(PAPER TRADING)</span>
        </h3>
        <span className="font-mono text-[10px] text-[rgba(255,255,255,0.6)]" suppressHydrationWarning>
          BAL: <span className="text-white font-bold" suppressHydrationWarning>${formatNumber(portfolio.usdt, 0)}</span>
        </span>
      </div>

      <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4 mb-4 z-10">
        <div className="flex-1 bg-[rgba(0,0,0,0.4)] rounded-lg p-3 border border-[rgba(255,255,255,0.05)]">
          <span className="block font-mono text-[9px] text-[rgba(255,255,255,0.4)] mb-1">ASSET HELD</span>
          <div className="font-orbitron text-lg text-white font-bold" suppressHydrationWarning>
            {formatNumber(assetBalance, 4)} <span className="text-xs text-[#00F0FF]">{chartSymbol.replace("USDT","")}</span>
          </div>
          <span className="block font-mono text-[9px] text-[rgba(0,255,102,0.8)] mt-1" suppressHydrationWarning>
            ≈ ${formatNumber(assetValueUsd, 2)}
          </span>
        </div>

        <div className="flex-1 flex flex-col justify-center">
          <span className="block font-mono text-[9px] text-[rgba(255,255,255,0.4)] mb-1">ORDER SIZE (USD)</span>
          <input
            type="number"
            value={amountUsd}
            onChange={(e) => setAmountUsd(e.target.value)}
            className="w-full bg-[rgba(0,240,255,0.05)] border border-[rgba(0,240,255,0.3)] text-white font-mono text-lg py-2 px-3 rounded outline-none focus:border-[#00F0FF] transition-colors"
          />
        </div>
      </div>

      <div className="flex space-x-4 z-10">
        <button
          onClick={() => handleTrade("BUY")}
          className="flex-1 py-3 bg-[rgba(0,255,102,0.1)] border border-[#00FF66] text-[#00FF66] font-orbitron font-bold rounded-lg hover:bg-[rgba(0,255,102,0.2)] hover:shadow-[0_0_15px_rgba(0,255,102,0.5)] transition-all"
        >
          BUY MKT
        </button>
        <button
          onClick={() => handleTrade("SELL")}
          className="flex-1 py-3 bg-[rgba(255,85,0,0.1)] border border-[#FF5500] text-[#FF5500] font-orbitron font-bold rounded-lg hover:bg-[rgba(255,85,0,0.2)] hover:shadow-[0_0_15px_rgba(255,85,0,0.5)] transition-all"
        >
          SELL MKT
        </button>
      </div>
    </div>
  );
}
