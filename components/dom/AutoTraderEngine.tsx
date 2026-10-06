"use client";

import React, { useEffect, useState, useRef } from "react";
import { useOmniStore } from "../../store/omniStore";
import { smaCrossoverStrategy } from "../../lib/backtest";

export default function AutoTraderEngine() {
  const autoTradeEnabled = useOmniStore(state => state.autoTradeEnabled);
  const toggleAutoTrade = useOmniStore(state => state.toggleAutoTrade);
  const aiExecutionLogs = useOmniStore(state => state.aiExecutionLogs);
  const latestCandle = useOmniStore(state => state.latestCandle);

  const [candleBuffer, setCandleBuffer] = useState<any[]>([]);
  const candleBufferRef = useRef<any[]>([]);

  useEffect(() => {
    if (latestCandle) {
      setCandleBuffer(prev => {
        // Handle identical timestamps to avoid repeating last candle
        const isDuplicate = prev.length > 0 && prev[prev.length - 1].time === latestCandle.time;
        
        let next;
        if (isDuplicate) {
          next = [...prev.slice(0, -1), latestCandle];
        } else {
          next = [...prev, latestCandle];
        }

        if (next.length > 50) return next.slice(next.length - 50);
        return next;
      });
    }
  }, [latestCandle]);

  useEffect(() => {
    candleBufferRef.current = candleBuffer;
  }, [candleBuffer]);

  useEffect(() => {
    if (!autoTradeEnabled) return;

    const intervalId = setInterval(() => {
      const state = useOmniStore.getState();
      const currentCandles = candleBufferRef.current;
      
      if (currentCandles.length < 26) return;

      const symbol = state.chartSymbol;
      const ticker = state.tickers[symbol];
      if (!ticker) return;

      const currentPrice = parseFloat(ticker.price);
      if (isNaN(currentPrice)) return;

      const signal = smaCrossoverStrategy(currentCandles, currentCandles.length - 1, false);

      if (signal === "BUY" && state.portfolio.usdt > 10000) {
        state.executeTrade(symbol, "BUY", 10000, currentPrice);
        state.addAILog({
          time: new Date().toLocaleTimeString("en-US", { hour12: false, timeZone: "UTC", hour: "2-digit", minute: "2-digit", second: "2-digit" }),
          action: "EXECUTED BUY",
          reason: "GOLDEN CROSS DETECTED",
          color: "#00FF66"
        });
      } else if (signal === "SELL" && (state.portfolio.assets[symbol] || 0) > 0) {
        const qty = state.portfolio.assets[symbol];
        const value = qty * currentPrice;
        state.executeTrade(symbol, "SELL", value, currentPrice);
        state.addAILog({
          time: new Date().toLocaleTimeString("en-US", { hour12: false, timeZone: "UTC", hour: "2-digit", minute: "2-digit", second: "2-digit" }),
          action: "EXECUTED SELL",
          reason: "OVERBOUGHT / DEATH CROSS",
          color: "#FF0055"
        });
      }
    }, 2000);

    return () => clearInterval(intervalId);
  }, [autoTradeEnabled]);

  return (
    <div className="border border-[rgba(0,240,255,0.3)] bg-[rgba(5,15,25,0.4)] backdrop-blur-md rounded-2xl p-4 flex flex-col h-[250px] relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-[#00F0FF]/5 to-transparent pointer-events-none" />
      <div className="flex justify-between items-center mb-4 z-10">
        <h3 className="font-orbitron font-bold text-[#00F0FF] text-[10px] tracking-widest flex items-center">
          <span className={`w-2 h-2 rounded-full mr-2 ${autoTradeEnabled ? "bg-[#00FF66] shadow-[0_0_8px_#00FF66] animate-pulse" : "bg-gray-600"}`} />
          SKYNET AUTO-TRADER
        </h3>
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            className="sr-only peer"
            checked={autoTradeEnabled}
            onChange={toggleAutoTrade}
          />
          <div className="w-9 h-5 bg-[rgba(255,255,255,0.1)] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#00F0FF] shadow-[0_0_10px_rgba(0,240,255,0.2)]"></div>
        </label>
      </div>

      <div className="flex-1 bg-[rgba(0,0,0,0.6)] rounded-lg p-3 font-mono text-[10px] overflow-y-auto space-y-2 border border-[rgba(255,255,255,0.05)] z-10">
        {aiExecutionLogs.length === 0 ? (
          <div className="text-[rgba(255,255,255,0.3)] h-full flex flex-col items-center justify-center space-y-2">
            <span className="text-lg">🤖</span>
            <span>{autoTradeEnabled ? "ANALYZING MARKET..." : "SYSTEM STANDBY"}</span>
          </div>
        ) : (
          aiExecutionLogs.map(log => (
            <div key={log.id} className="flex flex-col border-b border-[rgba(255,255,255,0.05)] pb-2 last:border-0 last:pb-0">
              <div className="flex justify-between">
                <span className="text-[rgba(255,255,255,0.5)]">{log.time}</span>
                <span style={{ color: log.color }} className="font-bold tracking-wider">{log.action}</span>
              </div>
              <div className="text-[rgba(255,255,255,0.7)] text-[9px] mt-1 flex items-start">
                <span className="text-[#00F0FF] mr-1">›</span> {log.reason}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
