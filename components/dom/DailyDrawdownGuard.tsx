"use client";

import React, { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useOmniStore } from "../../store/omniStore";

/**
 * DailyDrawdownGuard — Monitors daily P&L and auto-pauses trading if max drawdown is exceeded.
 * 
 * - Tracks portfolio value from session start
 * - If daily drawdown exceeds threshold (-5% default), shows warning and disables AutoTrader
 * - Renders as a slim status bar at the top of the trading interface
 */

interface Props {
  maxDailyDrawdownPct?: number; // default 5%
}

export default function DailyDrawdownGuard({ maxDailyDrawdownPct = 5 }: Props) {
  const portfolio = useOmniStore((state) => state.portfolio);
  const tickers = useOmniStore((state) => state.tickers);

  const [sessionStartValue, setSessionStartValue] = useState<number | null>(null);
  const [isTriggered, setIsTriggered] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const triggeredRef = useRef(false);

  // Calculate current portfolio value
  const currentValue =
    portfolio.usdt +
    Object.entries(portfolio.assets).reduce((acc, [sym, qty]) => {
      const ticker = tickers[sym];
      return acc + (ticker ? qty * parseFloat(ticker.price) : 0);
    }, 0);

  // Capture session start value on first render with valid data
  useEffect(() => {
    if (sessionStartValue === null && currentValue > 0) {
      setSessionStartValue(currentValue);
    }
  }, [currentValue, sessionStartValue]);

  // Check drawdown
  const drawdownPct = sessionStartValue
    ? ((sessionStartValue - currentValue) / sessionStartValue) * 100
    : 0;

  const isAboveThreshold = drawdownPct > maxDailyDrawdownPct;

  useEffect(() => {
    if (isAboveThreshold && !triggeredRef.current) {
      triggeredRef.current = true;
      setIsTriggered(true);

      // Auto-disable AutoTrader
      const store = useOmniStore.getState();
      if ("autoTradeEnabled" in store && store.autoTradeEnabled) {
        (store as any).toggleAutoTrade?.();
      }
    }
  }, [isAboveThreshold]);

  if (dismissed || sessionStartValue === null) return null;

  const drawdownColor =
    drawdownPct > maxDailyDrawdownPct
      ? "#FF0055"
      : drawdownPct > maxDailyDrawdownPct * 0.7
      ? "#FF5500"
      : drawdownPct > maxDailyDrawdownPct * 0.4
      ? "#FFA500"
      : "#00FF66";

  const barWidth = Math.min(100, (drawdownPct / maxDailyDrawdownPct) * 100);

  return (
    <>
      {/* Slim Status Bar */}
      <div className="w-full border-b border-[rgba(255,255,255,0.05)] bg-[rgba(5,5,15,0.6)] px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="font-mono text-[8px] text-[rgba(255,255,255,0.4)]">DAILY DRAWDOWN GUARD</span>
          <div className="w-32 h-1.5 bg-[rgba(255,255,255,0.05)] rounded-full overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{ backgroundColor: drawdownColor }}
              animate={{ width: `${barWidth}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
          <span className="font-mono text-[10px] font-bold" style={{ color: drawdownColor }}>
            {drawdownPct > 0 ? "-" : "+"}{Math.abs(drawdownPct).toFixed(2)}%
          </span>
          <span className="font-mono text-[8px] text-[rgba(255,255,255,0.3)]">
            / -{maxDailyDrawdownPct}% max
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="font-mono text-[9px] text-[rgba(255,255,255,0.4)]">
            SESSION: ${sessionStartValue.toLocaleString(undefined, { maximumFractionDigits: 0 })} → ${currentValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </span>
          {isTriggered && (
            <span className="font-mono text-[8px] text-[#FF0055] font-bold animate-pulse">
              ⚠ TRADING PAUSED
            </span>
          )}
        </div>
      </div>

      {/* Full-width Warning Banner */}
      <AnimatePresence>
        {isTriggered && !dismissed && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="w-full bg-[rgba(255,0,85,0.1)] border-b-2 border-[#FF0055] px-6 py-3 flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <span className="text-xl animate-pulse">🛑</span>
              <div>
                <span className="font-orbitron text-xs text-[#FF0055] font-bold tracking-wider">
                  MAX DAILY DRAWDOWN EXCEEDED
                </span>
                <span className="block font-mono text-[10px] text-[rgba(255,255,255,0.5)]">
                  AutoTrader has been automatically disabled. Daily loss: -{drawdownPct.toFixed(2)}% (limit: -{maxDailyDrawdownPct}%)
                </span>
              </div>
            </div>
            <button
              onClick={() => setDismissed(true)}
              className="font-mono text-[9px] text-[rgba(255,255,255,0.4)] hover:text-white border border-[rgba(255,255,255,0.1)] px-3 py-1 rounded transition-colors"
            >
              DISMISS
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
