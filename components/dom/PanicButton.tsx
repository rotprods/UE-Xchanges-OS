"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useOmniStore } from "../../store/omniStore";

/**
 * PanicButton — Emergency kill switch that closes all positions in 1 click.
 * 
 * Features:
 * - Big red button always visible in the corner
 * - Requires double-click confirmation (prevent accidental triggers)
 * - Closes all open positions by selling all assets at market
 * - Disables AutoTrader
 * - Shows confirmation modal with countdown
 */
export default function PanicButton() {
  const [showConfirm, setShowConfirm] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const portfolio = useOmniStore((state) => state.portfolio);
  const executeTrade = useOmniStore((state) => state.executeTrade);
  const tickers = useOmniStore((state) => state.tickers);

  const hasOpenPositions = Object.keys(portfolio.assets).some(
    (sym) => portfolio.assets[sym] > 0
  );

  const handlePanic = async () => {
    setExecuting(true);
    let closedCount = 0;

    try {
      // Disable auto-trader if it exists
      const store = useOmniStore.getState();
      if ("autoTradeEnabled" in store && store.autoTradeEnabled) {
        (store as any).toggleAutoTrade?.();
      }

      // Close all positions
      for (const [symbol, qty] of Object.entries(portfolio.assets)) {
        if (qty <= 0) continue;
        const ticker = tickers[symbol];
        if (!ticker) continue;

        const price = parseFloat(ticker.price);
        const amountUsd = qty * price;

        executeTrade(symbol, "SELL", amountUsd, price);
        closedCount++;
      }

      setResult(`✅ EMERGENCY CLOSE: ${closedCount} position${closedCount !== 1 ? "s" : ""} liquidated.`);
    } catch (err: any) {
      setResult(`⚠️ Error: ${err.message}`);
    } finally {
      setExecuting(false);
      setTimeout(() => {
        setShowConfirm(false);
        setResult(null);
      }, 5000);
    }
  };

  return (
    <>
      {/* Panic Button - Fixed position */}
      <motion.button
        onClick={() => setShowConfirm(true)}
        className="fixed bottom-6 right-6 z-[100] w-14 h-14 rounded-full flex items-center justify-center border-2 transition-all duration-300"
        style={{
          background: hasOpenPositions
            ? "radial-gradient(circle, #FF0055 0%, #990033 100%)"
            : "radial-gradient(circle, #333 0%, #1a1a1a 100%)",
          borderColor: hasOpenPositions ? "#FF0055" : "#444",
          boxShadow: hasOpenPositions
            ? "0 0 20px rgba(255,0,85,0.4), inset 0 0 10px rgba(255,0,85,0.2)"
            : "none",
        }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        title="PANIC — Close all positions"
      >
        <span className="text-white font-orbitron text-[8px] font-bold tracking-wider">
          EXIT
        </span>
      </motion.button>

      {/* Confirmation Modal */}
      <AnimatePresence>
        {showConfirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[200] bg-[rgba(0,0,0,0.8)] backdrop-blur-sm flex items-center justify-center"
            onClick={() => !executing && setShowConfirm(false)}
          >
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="border-2 border-[#FF0055] bg-[rgba(20,0,10,0.95)] backdrop-blur-xl rounded-2xl p-8 max-w-md w-full mx-4 text-center"
              style={{ boxShadow: "0 0 60px rgba(255,0,85,0.3)" }}
            >
              {/* Warning Icon */}
              <div className="w-20 h-20 mx-auto mb-4 rounded-full border-4 border-[#FF0055] flex items-center justify-center bg-[rgba(255,0,85,0.1)] animate-pulse">
                <span className="text-4xl">⚠️</span>
              </div>

              <h2 className="font-orbitron text-xl font-black text-[#FF0055] tracking-wider mb-2">
                EMERGENCY EXIT
              </h2>
              <p className="font-mono text-xs text-[rgba(255,255,255,0.6)] mb-6">
                This will immediately close ALL open positions at market price and disable AutoTrader.
              </p>

              {/* Positions Summary */}
              <div className="bg-[rgba(255,0,85,0.05)] border border-[rgba(255,0,85,0.2)] rounded-lg p-3 mb-6">
                <span className="font-mono text-[9px] text-[rgba(255,255,255,0.4)] block mb-2">POSITIONS TO CLOSE</span>
                {Object.entries(portfolio.assets).filter(([, qty]) => qty > 0).length === 0 ? (
                  <span className="font-mono text-xs text-[rgba(255,255,255,0.3)]">No open positions</span>
                ) : (
                  Object.entries(portfolio.assets)
                    .filter(([, qty]) => qty > 0)
                    .map(([sym, qty]) => {
                      const price = tickers[sym] ? parseFloat(tickers[sym].price) : 0;
                      return (
                        <div key={sym} className="flex justify-between font-mono text-xs py-1">
                          <span className="text-white">{sym}</span>
                          <span className="text-[rgba(255,255,255,0.5)]">{qty.toFixed(4)}</span>
                          <span className="text-[#FF0055]">${(qty * price).toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                        </div>
                      );
                    })
                )}
              </div>

              {/* Result */}
              {result && (
                <div className="font-mono text-xs text-[#00FF66] mb-4 p-2 border border-[rgba(0,255,102,0.2)] rounded bg-[rgba(0,255,102,0.05)]">
                  {result}
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3">
                <button
                  onClick={() => setShowConfirm(false)}
                  disabled={executing}
                  className="flex-1 font-orbitron text-[10px] tracking-wider py-3 rounded-lg border border-[rgba(255,255,255,0.2)] text-[rgba(255,255,255,0.6)] hover:text-white hover:border-white transition-all disabled:opacity-30"
                >
                  CANCEL
                </button>
                <button
                  onClick={handlePanic}
                  disabled={executing || !hasOpenPositions}
                  className="flex-1 font-orbitron text-[10px] tracking-wider py-3 rounded-lg bg-[#FF0055] text-white font-bold hover:bg-[#E60050] transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                  style={{ boxShadow: "0 0 20px rgba(255,0,85,0.4)" }}
                >
                  {executing ? (
                    <span className="flex items-center justify-center gap-2">
                      <div className="w-3 h-3 border border-t-transparent border-white rounded-full animate-spin" />
                      CLOSING...
                    </span>
                  ) : (
                    "CONFIRM LIQUIDATION"
                  )}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
