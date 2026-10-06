"use client";

import React from "react";
import dynamic from "next/dynamic";
import CandleChart from "../../components/dom/CandleChart";
import TradingPanel from "../../components/dom/TradingPanel";
import SwarmManager from "../../components/dom/SwarmManager";
import AlertFeed from "../../components/dom/AlertFeed";
import BacktestPanel from "../../components/dom/BacktestPanel";
import AutoTraderEngine from "../../components/dom/AutoTraderEngine";
import PortfolioAnalytics from "../../components/dom/PortfolioAnalytics";
import { useOmniStore } from "../../store/omniStore";

const OrderBookCanvas = dynamic(() => import("../../components/canvas/OrderBookCanvas"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-t-transparent border-[#8B00FF] rounded-full animate-spin" />
    </div>
  ),
});

export default function TradingPage() {
  const portfolio = useOmniStore((state) => state.portfolio);
  const tickers = useOmniStore((state) => state.tickers);
  const chartSymbol = useOmniStore((state) => state.chartSymbol);
  const tradeHistory = useOmniStore((state) => state.tradeHistory);

  // Calculate total portfolio value
  const totalValue = portfolio.usdt + Object.entries(portfolio.assets).reduce((acc, [sym, qty]) => {
    const ticker = tickers[sym];
    return acc + (ticker ? qty * parseFloat(ticker.price) : 0);
  }, 0);

  const pnl = totalValue - 1000000;
  const pnlPct = ((totalValue - 1000000) / 1000000) * 100;

  return (
    <div className="p-6 space-y-6">
      {/* Portfolio Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="border border-[rgba(0,240,255,0.3)] bg-[rgba(5,15,25,0.4)] backdrop-blur-md rounded-xl p-4">
          <span className="block font-mono text-[9px] text-[rgba(255,255,255,0.4)]">TOTAL VALUE</span>
          <span className="block font-orbitron text-xl text-[#00F0FF] font-bold">
            ${totalValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </span>
        </div>
        <div className="border border-[rgba(0,240,255,0.3)] bg-[rgba(5,15,25,0.4)] backdrop-blur-md rounded-xl p-4">
          <span className="block font-mono text-[9px] text-[rgba(255,255,255,0.4)]">CASH (USDT)</span>
          <span className="block font-orbitron text-xl text-white font-bold">
            ${portfolio.usdt.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </span>
        </div>
        <div className="border border-[rgba(0,240,255,0.3)] bg-[rgba(5,15,25,0.4)] backdrop-blur-md rounded-xl p-4">
          <span className="block font-mono text-[9px] text-[rgba(255,255,255,0.4)]">UNREALIZED P&L</span>
          <span className={`block font-orbitron text-xl font-bold ${pnl >= 0 ? "text-[#00FF66]" : "text-[#FF0055]"}`}>
            {pnl >= 0 ? "+" : ""}{pnl.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </span>
        </div>
        <div className="border border-[rgba(0,240,255,0.3)] bg-[rgba(5,15,25,0.4)] backdrop-blur-md rounded-xl p-4">
          <span className="block font-mono text-[9px] text-[rgba(255,255,255,0.4)]">RETURN %</span>
          <span className={`block font-orbitron text-xl font-bold ${pnlPct >= 0 ? "text-[#00FF66]" : "text-[#FF0055]"}`}>
            {pnlPct >= 0 ? "+" : ""}{pnlPct.toFixed(2)}%
          </span>
        </div>
      </div>

      {/* Main Trading Layout */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Chart + Trading Panel (2 cols) */}
        <div className="xl:col-span-2 space-y-4">
          <div className="h-[50vh] border border-[rgba(0,240,255,0.3)] bg-[rgba(5,15,25,0.4)] backdrop-blur-md rounded-2xl p-4 relative overflow-hidden">
            <CandleChart />
          </div>
          <TradingPanel />
          <AutoTraderEngine />

          {/* Trade History */}
          <div className="border border-[rgba(0,240,255,0.3)] bg-[rgba(5,15,25,0.4)] backdrop-blur-md rounded-2xl p-4">
            <h3 className="font-orbitron font-bold text-[#00F0FF] text-[10px] tracking-widest mb-4 flex items-center">
              <span className="w-1.5 h-1.5 bg-[#00F0FF] rounded-full mr-2 animate-pulse" />
              TRADE HISTORY
              <span className="ml-2 text-[rgba(255,255,255,0.3)]">({tradeHistory.length})</span>
            </h3>
            {tradeHistory.length === 0 ? (
              <p className="text-[10px] font-mono text-[rgba(255,255,255,0.3)] text-center py-4">NO TRADES EXECUTED YET</p>
            ) : (
              <div className="space-y-1 max-h-[200px] overflow-y-auto">
                <div className="grid grid-cols-5 gap-2 font-mono text-[8px] text-[rgba(255,255,255,0.3)] mb-2 pb-1 border-b border-[rgba(255,255,255,0.05)]">
                  <span>TIME</span><span>ASSET</span><span>SIDE</span><span>PRICE</span><span>P&L</span>
                </div>
                {tradeHistory.slice(0, 20).map((trade) => (
                  <div key={trade.id} className="grid grid-cols-5 gap-2 font-mono text-[10px] border-b border-[rgba(255,255,255,0.03)] pb-1">
                    <span className="text-[rgba(255,255,255,0.4)]">
                      {new Date(trade.timestamp).toLocaleTimeString("en-US", { hour12: false, timeZone: "UTC", hour: "2-digit", minute: "2-digit" })}
                    </span>
                    <span className="text-white font-bold">{trade.symbol.replace("USDT", "")}</span>
                    <span className={trade.side === "BUY" ? "text-[#00F0FF] font-bold" : "text-[#FF5500] font-bold"}>{trade.side}</span>
                    <span className="text-white">${trade.price.toFixed(2)}</span>
                    <span className={trade.pnl !== undefined ? (trade.pnl >= 0 ? "text-[#00FF66] font-bold" : "text-[#FF0055] font-bold") : "text-[rgba(255,255,255,0.4)]"}>
                      {trade.pnl !== undefined ? `${trade.pnl >= 0 ? "+" : ""}$${trade.pnl.toFixed(0)}` : "—"}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <BacktestPanel />
        </div>

        {/* Right Column: OrderBook + Positions */}
        <div className="space-y-4">
          {/* 3D OrderBook */}
          <div className="h-[300px] border border-[rgba(139,0,255,0.3)] bg-[rgba(15,5,25,0.4)] backdrop-blur-md rounded-2xl relative overflow-hidden">
            <div className="absolute top-4 left-4 z-10">
              <h3 className="font-orbitron font-bold text-[#8B00FF] tracking-wider text-xs">DEPTH MAP</h3>
            </div>
            <OrderBookCanvas />
          </div>

          <PortfolioAnalytics />

          {/* Open Positions */}
          <div className="border border-[rgba(0,240,255,0.3)] bg-[rgba(5,15,25,0.4)] backdrop-blur-md rounded-2xl p-4">
            <h3 className="font-orbitron font-bold text-[#00F0FF] text-[10px] tracking-widest mb-4 flex items-center">
              <span className="w-1.5 h-1.5 bg-[#00F0FF] rounded-full mr-2 animate-pulse" />
              OPEN POSITIONS
            </h3>
            <div className="space-y-2">
              {Object.entries(portfolio.assets).filter(([_, qty]) => qty > 0).length === 0 ? (
                <p className="text-[10px] font-mono text-[rgba(255,255,255,0.3)] text-center py-4">NO OPEN POSITIONS</p>
              ) : (
                Object.entries(portfolio.assets).filter(([_, qty]) => qty > 0).map(([sym, qty]) => {
                  const ticker = tickers[sym];
                  const currentPrice = ticker ? parseFloat(ticker.price) : 0;
                  const value = qty * currentPrice;
                  return (
                    <div key={sym} className="flex justify-between items-center text-xs font-mono border-b border-[rgba(255,255,255,0.05)] pb-2">
                      <span className="text-[#00F0FF] font-bold">{sym.replace("USDT", "")}</span>
                      <span className="text-[rgba(255,255,255,0.6)]">{qty.toFixed(4)}</span>
                      <span className="text-white">${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Event Feed */}
          <div className="h-[250px] border border-[rgba(0,240,255,0.3)] bg-[rgba(5,15,25,0.4)] backdrop-blur-md rounded-2xl p-4 overflow-hidden">
            <AlertFeed />
          </div>

          {/* Swarm */}
          <SwarmManager />
        </div>
      </div>
    </div>
  );
}
