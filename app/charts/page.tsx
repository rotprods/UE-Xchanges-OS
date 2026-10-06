"use client";

import React, { useEffect, useState, useRef } from "react";
import CandleChart from "../../components/dom/CandleChart";
import TradingPanel from "../../components/dom/TradingPanel";
import { useOmniStore } from "../../store/omniStore";
import { fetchHistoricalKlines } from "../../lib/api/binanceRest";
import { calculateSMA, calculateEMA, calculateRSI, calculateMACD, calculateBollingerBands } from "../../lib/indicators";

const INDICATORS = [
  { id: "sma7", label: "SMA 7", color: "#00F0FF", active: false },
  { id: "sma25", label: "SMA 25", color: "#8B00FF", active: false },
  { id: "ema12", label: "EMA 12", color: "#FF5500", active: false },
  { id: "bb", label: "Bollinger", color: "#00FF66", active: false },
  { id: "rsi", label: "RSI 14", color: "#FFD700", active: false },
  { id: "macd", label: "MACD", color: "#FF00FF", active: false },
];

export default function ChartsPage() {
  const chartSymbol = useOmniStore((state) => state.chartSymbol);
  const chartInterval = useOmniStore((state) => state.chartInterval);
  const setChartSymbol = useOmniStore((state) => state.setChartSymbol);
  const setChartInterval = useOmniStore((state) => state.setChartInterval);
  const marketMode = useOmniStore((state) => state.marketMode);
  const tickers = useOmniStore((state) => state.tickers);

  const [activeIndicators, setActiveIndicators] = useState<Record<string, boolean>>({});
  const [historicalData, setHistoricalData] = useState<any[]>([]);
  const [indicatorData, setIndicatorData] = useState<Record<string, any>>({});

  const watchedCrypto = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "TRXUSDT", "TONUSDT", "LINKUSDT", "HBARUSDT", "XLMUSDT"];
  const watchedStocks = ["NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "SPY", "GME", "AMC"];
  const symbols = marketMode === "CRYPTO" ? watchedCrypto : watchedStocks;
  const intervals = ["1s", "1m", "15m", "1h", "4h", "1d", "1w", "1M"];

  // Fetch historical data on symbol/interval change
  useEffect(() => {
    if (marketMode !== "CRYPTO") return;
    
    const loadHistory = async () => {
      try {
        const candles = await fetchHistoricalKlines(chartSymbol, chartInterval, 500);
        setHistoricalData(candles);
      } catch (e) {
        console.error("Failed to fetch historical klines:", e);
      }
    };
    loadHistory();
  }, [chartSymbol, chartInterval, marketMode]);

  // Calculate indicators when historical data or active indicators change
  useEffect(() => {
    if (historicalData.length === 0) return;

    const result: Record<string, any> = {};

    if (activeIndicators["sma7"]) {
      result.sma7 = calculateSMA(historicalData, 7);
    }
    if (activeIndicators["sma25"]) {
      result.sma25 = calculateSMA(historicalData, 25);
    }
    if (activeIndicators["ema12"]) {
      result.ema12 = calculateEMA(historicalData, 12);
    }
    if (activeIndicators["bb"]) {
      result.bb = calculateBollingerBands(historicalData);
    }
    if (activeIndicators["rsi"]) {
      result.rsi = calculateRSI(historicalData, 14);
    }
    if (activeIndicators["macd"]) {
      result.macd = calculateMACD(historicalData);
    }

    setIndicatorData(result);
  }, [historicalData, activeIndicators]);

  const toggleIndicator = (id: string) => {
    setActiveIndicators((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="p-6 space-y-6">
      {/* Controls Bar */}
      <div className="flex flex-wrap items-center gap-4">
        {/* Symbol Selector */}
        <div className="flex items-center space-x-2">
          <span className="font-mono text-[9px] text-[rgba(255,255,255,0.4)]">SYMBOL</span>
          <select
            value={chartSymbol}
            onChange={(e) => setChartSymbol(e.target.value)}
            className="bg-[rgba(0,240,255,0.05)] border border-[rgba(0,240,255,0.3)] text-[#00F0FF] font-mono text-xs px-3 py-2 rounded-lg outline-none"
          >
            {symbols.map((sym) => (
              <option key={sym} value={sym} className="bg-[#0A0A14] text-white">{sym}</option>
            ))}
          </select>
        </div>

        {/* Interval Selector */}
        <div className="flex items-center bg-[rgba(0,0,0,0.4)] rounded-lg border border-[rgba(255,255,255,0.1)] overflow-hidden">
          {intervals.map((int) => (
            <button
              key={int}
              onClick={() => setChartInterval(int)}
              className={`px-3 py-2 text-[10px] font-mono transition-all ${
                chartInterval === int
                  ? "bg-[rgba(0,240,255,0.15)] text-[#00F0FF]"
                  : "text-[rgba(255,255,255,0.4)] hover:text-white"
              }`}
            >
              {int}
            </button>
          ))}
        </div>

        {/* Indicator Toggles */}
        <div className="flex items-center space-x-1">
          {INDICATORS.map((ind) => (
            <button
              key={ind.id}
              onClick={() => toggleIndicator(ind.id)}
              className={`px-3 py-2 text-[9px] font-orbitron font-bold rounded-lg border transition-all ${
                activeIndicators[ind.id]
                  ? `border-[${ind.color}] bg-[${ind.color}15] shadow-[0_0_8px_${ind.color}33]`
                  : "border-[rgba(255,255,255,0.1)] text-[rgba(255,255,255,0.4)] hover:text-white"
              }`}
              style={activeIndicators[ind.id] ? { borderColor: ind.color, color: ind.color, backgroundColor: `${ind.color}15` } : {}}
            >
              {ind.label}
            </button>
          ))}
        </div>
      </div>

      {/* Stats Bar */}
      {(() => {
        const ticker = tickers[chartSymbol];
        const price   = ticker ? parseFloat(ticker.price)       : null;
        const high24  = ticker ? parseFloat(ticker.high)        : null;
        const low24   = ticker ? parseFloat(ticker.low)         : null;
        const vol24   = ticker ? parseFloat(ticker.volumeQuote) : null;
        const fmtP = (v: number | null) =>
          v === null ? "—" :
          v >= 1000 ? `$${v.toLocaleString(undefined, { maximumFractionDigits: 0 })}` :
          `$${v.toFixed(v >= 1 ? 2 : 4)}`;
        const fmtV = (v: number | null) =>
          v === null ? "—" :
          v >= 1e9  ? `$${(v / 1e9).toFixed(2)}B` :
          v >= 1e6  ? `$${(v / 1e6).toFixed(2)}M` :
          `$${v.toFixed(0)}`;
        const statItems: { label: string; value: string; color: string }[] = [
          { label: "PRICE",      value: fmtP(price),  color: "#00F0FF" },
          { label: "24H HIGH",   value: fmtP(high24), color: "#00FF66" },
          { label: "24H LOW",    value: fmtP(low24),  color: "#FF0055" },
          { label: "24H VOLUME", value: fmtV(vol24),  color: "#8B00FF" },
        ];
        return (
          <div className="flex flex-wrap items-center gap-x-6 gap-y-2 px-4 py-2 border border-[rgba(0,240,255,0.1)] bg-[rgba(5,15,25,0.5)] backdrop-blur-md rounded-xl">
            {statItems.map(({ label, value, color }) => (
              <div key={label} className="flex items-center gap-2">
                <span className="font-mono text-[8px] tracking-widest" style={{ color: `${color}80` }}>{label}</span>
                <span className="font-orbitron text-xs font-bold" style={{ color }}>{value}</span>
              </div>
            ))}
          </div>
        );
      })()}

      {/* Main Chart */}
      <div className="h-[60vh] border border-[rgba(0,240,255,0.3)] bg-[rgba(5,15,25,0.4)] backdrop-blur-md rounded-2xl p-4 relative overflow-hidden">
        <CandleChart />
      </div>

      {/* RSI Sub-Chart */}
      {activeIndicators["rsi"] && indicatorData.rsi && (
        <div className="h-[150px] border border-[rgba(255,215,0,0.3)] bg-[rgba(5,15,25,0.4)] backdrop-blur-md rounded-2xl p-4 relative overflow-hidden">
          <h4 className="font-orbitron text-[10px] text-[#FFD700] tracking-wider mb-2">RSI (14)</h4>
          <div className="flex items-end h-[100px] space-x-px">
            {indicatorData.rsi.slice(-100).map((val: number | null, i: number) => {
              if (val === null) return <div key={i} className="flex-1" />;
              const height = val;
              const isOverbought = val > 70;
              const isOversold = val < 30;
              return (
                <div key={i} className="flex-1 flex flex-col justify-end">
                  <div
                    className="w-full rounded-t-sm transition-all"
                    style={{
                      height: `${height}%`,
                      backgroundColor: isOverbought ? "#FF0055" : isOversold ? "#00FF66" : "#FFD700",
                      opacity: 0.6,
                    }}
                  />
                </div>
              );
            })}
          </div>
          <div className="flex justify-between mt-1 text-[8px] font-mono text-[rgba(255,255,255,0.3)]">
            <span>Oversold (30)</span>
            <span>RSI: {indicatorData.rsi[indicatorData.rsi.length - 1]?.toFixed(1) || "—"}</span>
            <span>Overbought (70)</span>
          </div>
        </div>
      )}

      {/* MACD Sub-Chart */}
      {activeIndicators["macd"] && indicatorData.macd && (
        <div className="h-[150px] border border-[rgba(255,0,255,0.3)] bg-[rgba(5,15,25,0.4)] backdrop-blur-md rounded-2xl p-4 relative overflow-hidden">
          <h4 className="font-orbitron text-[10px] text-[#FF00FF] tracking-wider mb-2">MACD (12, 26, 9)</h4>
          <div className="flex items-center h-[100px] space-x-px">
            {indicatorData.macd.histogram.slice(-100).map((val: number | null, i: number) => {
              if (val === null) return <div key={i} className="flex-1" />;
              const isPositive = val >= 0;
              const absVal = Math.abs(val);
              const maxVal = Math.max(...indicatorData.macd.histogram.filter((v: any) => v !== null).map((v: any) => Math.abs(v)));
              const heightPct = maxVal > 0 ? (absVal / maxVal) * 50 : 0;
              return (
                <div key={i} className="flex-1 flex flex-col items-center justify-center h-full relative">
                  <div
                    className="w-full absolute"
                    style={{
                      height: `${heightPct}%`,
                      backgroundColor: isPositive ? "#00FF66" : "#FF0055",
                      opacity: 0.7,
                      ...(isPositive ? { bottom: "50%" } : { top: "50%" }),
                    }}
                  />
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Trading Panel */}
      <TradingPanel />
    </div>
  );
}
