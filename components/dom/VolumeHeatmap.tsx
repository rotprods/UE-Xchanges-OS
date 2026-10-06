"use client";

import React, { useRef, useState, useEffect } from "react";
import { TickerData } from "../../workers/ticker.worker";
import { useOmniStore } from "../../store/omniStore";

interface VolumeHeatmapProps {
  tickers: Record<string, TickerData>;
  totalVolume: number;
}

export default function VolumeHeatmap({ tickers, totalVolume }: VolumeHeatmapProps) {
  const prevPrices = useRef<Record<string, number>>({});
  
  const marketMode = useOmniStore((state) => state.marketMode);
  const setMarketMode = useOmniStore((state) => state.setMarketMode);
  const setChartSymbol = useOmniStore((state) => state.setChartSymbol);

  // Trending Tab State
  const [activeTab, setActiveTab] = useState<"CRYPTO" | "STOCKS" | "TRENDING">("CRYPTO");
  const [trendingCoins, setTrendingCoins] = useState<any[]>([]);
  const [isLoadingTrending, setIsLoadingTrending] = useState(false);

  useEffect(() => {
    // Sync external marketMode with activeTab
    if (marketMode === "CRYPTO" && activeTab !== "CRYPTO" && activeTab !== "TRENDING") {
      setActiveTab("CRYPTO");
    } else if (marketMode === "STOCKS" && activeTab !== "STOCKS") {
      setActiveTab("STOCKS");
    }
  }, [marketMode]);

  useEffect(() => {
    if (activeTab === "TRENDING" && trendingCoins.length === 0) {
      setIsLoadingTrending(true);
      fetch("https://api.coingecko.com/api/v3/search/trending")
        .then(res => res.json())
        .then(data => {
          if (data && data.coins) {
            setTrendingCoins(data.coins.slice(0, 10)); // Top 10 trending
          }
          setIsLoadingTrending(false);
        })
        .catch(err => {
          console.error("CoinGecko fetch error:", err);
          setIsLoadingTrending(false);
        });
    }
  }, [activeTab]);

  const getPriceDirection = (symbol: string, currentPrice: number) => {
    const prev = prevPrices.current[symbol];
    prevPrices.current[symbol] = currentPrice;
    
    if (!prev || prev === currentPrice) return "neutral";
    return currentPrice > prev ? "up" : "down";
  };

  const handleTabSwitch = (tab: "CRYPTO" | "STOCKS" | "TRENDING") => {
    setActiveTab(tab);
    if (tab === "STOCKS") {
      setMarketMode("STOCKS");
      setChartSymbol("NVDA");
    } else if (tab === "CRYPTO") {
      setMarketMode("CRYPTO");
      setChartSymbol("BTCUSDT");
    }
    // If TRENDING, we keep marketMode as CRYPTO usually to not break worker
  };

  const currentList = Object.values(tickers).sort((a, b) => {
    if (activeTab === "CRYPTO" || activeTab === "TRENDING") {
      const order = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "TRXUSDT", "TONUSDT", "LINKUSDT", "HBARUSDT", "XLMUSDT"];
      const indexA = order.indexOf(a.symbol);
      const indexB = order.indexOf(b.symbol);
      if (indexA === -1 && indexB === -1) return 0;
      if (indexA === -1) return 1;
      if (indexB === -1) return -1;
      return indexA - indexB;
    } else {
      // Stocks Order
      const order = ["NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "SPY", "GME", "AMC"];
      const indexA = order.indexOf(a.symbol);
      const indexB = order.indexOf(b.symbol);
      if (indexA === -1 && indexB === -1) return 0;
      if (indexA === -1) return 1;
      if (indexB === -1) return -1;
      return indexA - indexB;
    }
  });

  return (
    <div className="glass-panel rounded-xl w-full flex flex-col h-[340px] pointer-events-auto">
      {/* Tabs */}
      <div className="flex border-b border-[rgba(0,240,255,0.1)]">
        <button 
          onClick={() => handleTabSwitch("CRYPTO")}
          className={`flex-1 py-3 text-[10px] sm:text-xs font-orbitron font-bold transition-all duration-300 rounded-tl-xl ${
            activeTab === "CRYPTO" 
              ? "bg-[rgba(0,240,255,0.1)] text-[#00F0FF] border-b-2 border-[#00F0FF]" 
              : "text-[rgba(255,255,255,0.4)] hover:bg-[rgba(255,255,255,0.02)]"
          }`}
        >
          CRYPTO
        </button>
        <button 
          onClick={() => handleTabSwitch("STOCKS")}
          className={`flex-1 py-3 text-[10px] sm:text-xs font-orbitron font-bold transition-all duration-300 ${
            activeTab === "STOCKS" 
              ? "bg-[rgba(139,0,255,0.1)] text-[#E024FF] border-b-2 border-[#E024FF]" 
              : "text-[rgba(255,255,255,0.4)] hover:bg-[rgba(255,255,255,0.02)]"
          }`}
        >
          EQUITIES
        </button>
        <button 
          onClick={() => handleTabSwitch("TRENDING")}
          className={`flex-1 py-3 text-[10px] sm:text-xs font-orbitron font-bold transition-all duration-300 rounded-tr-xl flex items-center justify-center ${
            activeTab === "TRENDING" 
              ? "bg-[rgba(255,85,0,0.1)] text-[#FF5500] border-b-2 border-[#FF5500]" 
              : "text-[rgba(255,255,255,0.4)] hover:bg-[rgba(255,255,255,0.02)]"
          }`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[#FF5500] mr-1.5 animate-pulse"></span>
          TRENDS
        </button>
      </div>

      <div className="p-4 flex-1 flex flex-col overflow-hidden">
        {/* Global Volume statistics (Hide on Trending) */}
        {activeTab !== "TRENDING" && (
          <div className={`bg-[rgba(139,0,255,0.03)] border rounded-lg p-2 mb-3 transition-colors ${
              activeTab === "CRYPTO" ? "border-[rgba(0,240,255,0.15)]" : "border-[rgba(224,36,255,0.15)]"
            }`}>
            <span className={`font-mono text-[9px] ${activeTab === "CRYPTO" ? "text-[#00F0FF]" : "text-[#E024FF]"}`}>
              {activeTab === "CRYPTO" ? "ACCUMULATED VOLUME TRADED (24H)" : "ALGORITHMIC TRADING VOLUME"}
            </span>
            <div className="font-orbitron font-black text-lg text-white text-glow">
              ${totalVolume > 0 ? (totalVolume / 1000000).toFixed(2) : "0.00"} M <span className="font-mono text-xs text-[rgba(255,255,255,0.5)]">USD</span>
            </div>
          </div>
        )}

        {/* Tickers List */}
        <div className="flex-1 overflow-y-auto pr-1 space-y-2">
          {activeTab === "TRENDING" ? (
             isLoadingTrending ? (
               <div className="flex flex-col items-center justify-center h-full text-[10px] font-mono text-[#FF5500]">
                 <span className="animate-pulse">FETCHING GLOBAL TRENDS...</span>
               </div>
             ) : (
               trendingCoins.map((coin, i) => {
                 const change = coin.item.data.price_change_percentage_24h?.usd || 0;
                 const isPositive = change >= 0;
                 return (
                  <div
                    key={coin.item.id}
                    className="flex items-center justify-between p-2 rounded bg-[rgba(255,85,0,0.03)] border border-[rgba(255,85,0,0.1)] hover:border-[#FF5500] transition-colors duration-200"
                  >
                    <div className="flex items-center space-x-3">
                      <span className="font-mono text-xs text-[rgba(255,255,255,0.3)]">#{i+1}</span>
                      <img src={coin.item.thumb} alt="icon" className="w-5 h-5 rounded-full" />
                      <div className="flex flex-col">
                        <span className="font-orbitron text-xs font-bold text-white">{coin.item.symbol}</span>
                        <span className="font-mono text-[8px] text-[rgba(255,255,255,0.5)] truncate max-w-[80px]">{coin.item.name}</span>
                      </div>
                    </div>
                    <div className="flex flex-col text-right">
                      <span className="font-mono text-xs font-bold text-white">
                        {coin.item.data.price}
                      </span>
                      <span className={`font-mono text-[9px] ${isPositive ? "text-[#00FF66]" : "text-[#FF5500]"}`}>
                        {isPositive ? "+" : ""}{change.toFixed(2)}%
                      </span>
                    </div>
                  </div>
                 );
               })
             )
          ) : currentList.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-[10px] font-mono text-[rgba(255,255,255,0.4)]">
              <span className="animate-pulse">SYNCHRONIZING TELEMETRY...</span>
            </div>
          ) : (
            currentList.map((ticker) => {
              const priceNum = parseFloat(ticker.price);
              const direction = getPriceDirection(ticker.symbol, priceNum);
              const changePercent = ((priceNum - parseFloat(ticker.open)) / parseFloat(ticker.open)) * 100;
              const isPositive = changePercent >= 0;

              return (
                <div
                  key={ticker.symbol}
                  className="flex items-center justify-between p-2 rounded bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.04)] hover:border-[rgba(0,240,255,0.1)] transition-colors duration-200"
                >
                  <div className="flex flex-col">
                    <span className="font-orbitron text-xs font-bold text-white">{ticker.symbol.replace("USDT", "")}</span>
                    <span className="font-mono text-[8px] text-[rgba(255,255,255,0.4)]">
                      {activeTab === "CRYPTO" ? "USDT PAIR" : "STOCK"}
                    </span>
                  </div>
                  <div className="hidden sm:block font-mono text-[9px] text-right text-[rgba(255,255,255,0.4)] pr-4">
                    Vol: {Math.round(parseFloat(ticker.volumeQuote) / 1000)}k
                  </div>
                  <div className="flex flex-col text-right">
                    <span
                      className={`font-mono text-xs font-bold transition-all duration-300 ${
                        direction === "up" ? "text-[#00FF66] text-shadow-[0_0_8px_rgba(0,255,102,0.3)]"
                        : direction === "down" ? "text-[#FF5500] text-shadow-[0_0_8px_rgba(255,85,0,0.3)]"
                        : "text-white"
                      }`}
                    >
                      ${priceNum.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                    <span className={`font-mono text-[9px] ${isPositive ? "text-[#00FF66]" : "text-[#FF5500]"}`}>
                      {isPositive ? "+" : ""}{changePercent.toFixed(2)}%
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
