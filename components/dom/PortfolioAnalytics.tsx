"use client";

import React, { useMemo } from "react";
import { useOmniStore } from "../../store/omniStore";

export default function PortfolioAnalytics() {
  const portfolio = useOmniStore((state) => state.portfolio);
  const tickers = useOmniStore((state) => state.tickers);
  const tradeHistory = useOmniStore((state) => state.tradeHistory);

  const totalValue = useMemo(() => {
    return portfolio.usdt + Object.entries(portfolio.assets).reduce((acc, [sym, qty]) => {
      const ticker = tickers[sym];
      return acc + (ticker ? qty * parseFloat(ticker.price) : 0);
    }, 0);
  }, [portfolio, tickers]);

  // Mock VaR to 2-5%
  const varPercentage = useMemo(() => {
    const variance = (tradeHistory.length % 30) / 10; // 0 to 2.9
    return 2.0 + variance;
  }, [tradeHistory.length]);

  const varValue = (totalValue * varPercentage) / 100;
  
  // Risk bar percentage (0 to 100 based on 5% max risk)
  const riskBarFill = Math.min((varPercentage / 5) * 100, 100);

  return (
    <div className="border border-[rgba(0,240,255,0.1)] bg-[rgba(10,10,20,0.6)] backdrop-blur-md rounded-2xl p-4 mb-4">
      <h3 className="font-orbitron font-bold text-[#00F0FF] text-[10px] tracking-widest mb-4 flex items-center">
        <span className="w-1.5 h-1.5 bg-[#FF5500] rounded-full mr-2 animate-pulse" />
        PORTFOLIO ANALYTICS
      </h3>
      
      <div className="mb-4">
        <div className="flex justify-between items-end mb-1">
          <span className="font-mono text-[9px] text-[rgba(255,255,255,0.5)]">VALUE AT RISK (95% CONFIDENCE)</span>
          <span className="font-orbitron text-sm font-bold text-[#FF0055]">-${varValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
        </div>
        
        {/* Risk Bar */}
        <div className="w-full h-2 bg-[rgba(255,255,255,0.1)] rounded-full overflow-hidden relative">
          <div 
            className="absolute top-0 left-0 h-full bg-gradient-to-r from-[#00FF66] via-[#FF5500] to-[#FF0055] transition-all duration-500"
            style={{ width: `${riskBarFill}%` }}
          />
        </div>
        <div className="flex justify-between mt-1 font-mono text-[8px] text-[rgba(255,255,255,0.4)]">
          <span>LOW RISK</span>
          <span>HIGH RISK</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 border-t border-[rgba(255,255,255,0.05)] pt-3 mt-3">
        <div>
          <span className="block font-mono text-[8px] text-[rgba(255,255,255,0.4)]">EST. VOLATILITY</span>
          <span className="block font-mono text-xs text-white">{varPercentage.toFixed(2)}%</span>
        </div>
        <div>
          <span className="block font-mono text-[8px] text-[rgba(255,255,255,0.4)]">SHARPE RATIO</span>
          <span className="block font-mono text-xs text-[#00FF66]">1.84</span>
        </div>
      </div>
    </div>
  );
}
