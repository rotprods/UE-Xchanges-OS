"use client";

import React, { useEffect, useState } from "react";
import { useOmniStore } from "../../store/omniStore";
import { motion } from "framer-motion";

interface ExchangePrice {
  name: string;
  bid: number;
  ask: number;
}

export default function ArbitrageScanner() {
  const tickers = useOmniStore((state) => state.tickers);
  const stats = useOmniStore((state) => state.stats);

  const baseSymbol = "BTCUSDT";
  const basePriceStr = tickers[baseSymbol]?.price;
  const basePrice = basePriceStr ? parseFloat(basePriceStr) : 65000;

  const [exchanges, setExchanges] = useState<ExchangePrice[]>([
    { name: "Binance", bid: 0, ask: 0 },
    { name: "Coinbase", bid: 0, ask: 0 },
    { name: "Kraken", bid: 0, ask: 0 },
  ]);

  useEffect(() => {
    let isMounted = true;
    
    const fetchRealData = async () => {
      try {
        const res = await fetch("/api/arbitrage");
        const data = await res.json();

        if (!isMounted || !data.exchanges) return;

        setExchanges(data.exchanges);
      } catch (err) {
        console.error("Arbitrage API fetch error:", err);
      }
    };

    fetchRealData();
    const interval = setInterval(fetchRealData, 3000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const sortedBids = [...exchanges].sort((a, b) => b.bid - a.bid);
  const sortedAsks = [...exchanges].sort((a, b) => a.ask - b.ask);

  const highestBidExchange = sortedBids[0];
  const lowestAskExchange = sortedAsks[0];

  const spreadAmount = highestBidExchange.bid - lowestAskExchange.ask;
  const spreadProfitPct = lowestAskExchange.ask > 0 ? (spreadAmount / lowestAskExchange.ask) * 100 : 0;

  // Mock gas fee based on stats.gasGwei
  const gasFeeUsd = stats.gasGwei * 0.05;
  const estimatedNetProfit = spreadAmount - gasFeeUsd;

  return (
    <div className="border border-[rgba(0,240,255,0.1)] bg-[rgba(10,10,20,0.6)] backdrop-blur-md rounded-2xl p-6 relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-[rgba(0,240,255,0.05)] to-transparent pointer-events-none" />
      
      <div className="flex justify-between items-center mb-6">
        <h3 className="font-orbitron font-bold text-[#00F0FF] tracking-widest text-sm flex items-center">
          <span className="w-2 h-2 bg-[#00F0FF] rounded-full mr-2 animate-pulse shadow-[0_0_8px_#00F0FF]" />
          ARBITRAGE SCANNER <span className="ml-2 text-white opacity-50 text-[10px]">({baseSymbol})</span>
        </h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-[rgba(0,240,255,0.2)] font-mono text-[10px] text-[rgba(255,255,255,0.5)]">
              <th className="pb-2">EXCHANGE</th>
              <th className="pb-2 text-right">BID</th>
              <th className="pb-2 text-right">ASK</th>
            </tr>
          </thead>
          <tbody className="font-mono text-xs">
            {exchanges.map((ex) => {
              const isHighestBid = ex.name === highestBidExchange.name;
              const isLowestAsk = ex.name === lowestAskExchange.name;
              return (
                <tr key={ex.name} className="border-b border-[rgba(255,255,255,0.05)]">
                  <td className="py-3 text-[rgba(255,255,255,0.8)]">{ex.name}</td>
                  <td className={`py-3 text-right ${isHighestBid ? "text-[#00FF66] font-bold shadow-[0_0_10px_rgba(0,255,102,0.5)]" : "text-white"}`}>
                    ${ex.bid.toFixed(2)}
                  </td>
                  <td className={`py-3 text-right ${isLowestAsk ? "text-[#FF0055] font-bold shadow-[0_0_10px_rgba(255,0,85,0.5)]" : "text-white"}`}>
                    ${ex.ask.toFixed(2)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-6 pt-4 border-t border-[rgba(0,240,255,0.2)] grid grid-cols-2 gap-4">
        <div>
          <span className="block font-mono text-[9px] text-[rgba(255,255,255,0.5)]">SPREAD PROFIT %</span>
          <span className={`block font-orbitron text-lg font-bold ${spreadProfitPct > 0 ? "text-[#00FF66]" : "text-[rgba(255,255,255,0.5)]"}`}>
            {spreadProfitPct > 0 ? "+" : ""}{spreadProfitPct.toFixed(3)}%
          </span>
        </div>
        <div>
          <span className="block font-mono text-[9px] text-[rgba(255,255,255,0.5)]">EST. NET PROFIT</span>
          <span className={`block font-orbitron text-lg font-bold ${estimatedNetProfit > 0 ? "text-[#00FF66]" : "text-[rgba(255,255,255,0.5)]"}`}>
            {estimatedNetProfit > 0 ? "+" : ""}${estimatedNetProfit.toFixed(2)}
          </span>
        </div>
      </div>

      {estimatedNetProfit > 0 && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="mt-4 p-2 border border-[#00FF66] bg-[rgba(0,255,102,0.1)] text-[#00FF66] text-center font-orbitron text-xs font-bold tracking-widest rounded-md animate-pulse shadow-[0_0_10px_rgba(0,255,102,0.3)]"
        >
          ARBITRAGE OPPORTUNITY DETECTED
        </motion.div>
      )}
    </div>
  );
}
