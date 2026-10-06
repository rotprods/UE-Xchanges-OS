"use client";

import React, { useEffect, useRef, useState } from "react";
import { createChart, IChartApi, ISeriesApi, CandlestickSeries, LineSeries } from "lightweight-charts";
import { useOmniStore } from "../../store/omniStore";

const CRYPTO_SYMBOLS = [
  "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", 
  "DOGEUSDT", "ADAUSDT", "TRXUSDT", "TONUSDT", "LINKUSDT", 
  "HBARUSDT", "XLMUSDT"
];

const STOCK_SYMBOLS = [
  "NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "SPY", "GME", "AMC"
];

const INTERVALS = [
  { label: "1s", value: "1s" },
  { label: "1m", value: "1m" },
  { label: "15m", value: "15m" },
  { label: "1h", value: "1h" },
  { label: "4h", value: "4h" },
  { label: "1D", value: "1d" },
  { label: "1W", value: "1w" },
  { label: "1M", value: "1M" }
];

export default function CandleChart() {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const smaSeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const lastTimeRef = useRef<number>(0);
  const closesRef = useRef<number[]>([]);
  const timesRef = useRef<number[]>([]);
  
  const latestCandle = useOmniStore((state) => state.latestCandle);
  const chartSymbol = useOmniStore((state) => state.chartSymbol);
  const chartInterval = useOmniStore((state) => state.chartInterval);
  const marketMode = useOmniStore((state) => state.marketMode);
  
  const setChartSymbol = useOmniStore((state) => state.setChartSymbol);
  const setChartInterval = useOmniStore((state) => state.setChartInterval);
  
  const currentSymbols = marketMode === "CRYPTO" ? CRYPTO_SYMBOLS : STOCK_SYMBOLS;
  
  const [isLoading, setIsLoading] = useState(true);

  // Helper to calculate SMA
  const calculateSMA = (closes: number[], period: number = 20) => {
    const smaData = [];
    for (let i = 0; i < closes.length; i++) {
      if (i < period - 1) {
        // Not enough data
        continue;
      }
      let sum = 0;
      for (let j = 0; j < period; j++) {
        sum += closes[i - j];
      }
      smaData.push(sum / period);
    }
    return smaData;
  };

  // Initialize Chart and handle historical fetching
  useEffect(() => {
    if (!chartContainerRef.current) return;

    setIsLoading(true);
    // CLEAR THE LATEST CANDLE FROM PREVIOUS STATE TO PREVENT DESYNC CRASH
    useOmniStore.getState().setLatestCandle(null as any);
    lastTimeRef.current = 0;
    closesRef.current = [];
    timesRef.current = [];

    // Create TradingView Chart Instance (if not exists)
    if (!chartRef.current) {
      const chart = createChart(chartContainerRef.current, {
        layout: {
          background: { type: "solid" as any, color: "transparent" },
          textColor: "rgba(255, 255, 255, 0.6)",
        },
        grid: {
          vertLines: { color: "rgba(0, 240, 255, 0.05)" },
          horzLines: { color: "rgba(0, 240, 255, 0.05)" },
        },
        timeScale: {
          timeVisible: true,
          secondsVisible: chartInterval === "1s",
          borderColor: "rgba(0, 240, 255, 0.2)",
        },
        rightPriceScale: {
          borderColor: "rgba(0, 240, 255, 0.2)",
        },
        crosshair: {
          vertLine: {
            color: "#00F0FF",
            width: 1,
            style: 1,
            labelBackgroundColor: "#00F0FF",
          },
          horzLine: {
            color: "#00F0FF",
            width: 1,
            style: 1,
            labelBackgroundColor: "#00F0FF",
          },
        },
      });

      chartRef.current = chart;

      const candleSeries = chart.addSeries(CandlestickSeries, {
        upColor: "#00F0FF",       // Electric Cyan
        downColor: "#FF5500",     // Quantum Orange
        borderVisible: false,
        wickUpColor: "#00F0FF",
        wickDownColor: "#FF5500",
      });

      const smaSeries = chart.addSeries(LineSeries, {
        color: '#E024FF',         // Neon Purple/Pink for SMA
        lineWidth: 2,
        crosshairMarkerVisible: false,
      });

      seriesRef.current = candleSeries as any;
      smaSeriesRef.current = smaSeries as any;

      const handleResize = () => {
        if (chartContainerRef.current && chartRef.current) {
          chartRef.current.applyOptions({
            width: chartContainerRef.current.clientWidth,
            height: chartContainerRef.current.clientHeight,
          });
        }
      };

      window.addEventListener("resize", handleResize);
    } else {
      // Update timescale format when interval changes
      chartRef.current.applyOptions({
        timeScale: {
          secondsVisible: chartInterval === "1s",
        }
      });
      // Clear old series data
      if (seriesRef.current) {
        seriesRef.current.setData([]);
      }
      if (smaSeriesRef.current) {
        smaSeriesRef.current.setData([]);
      }
    }

    // Fetch Historical Data for the selected symbol and interval
    let isMounted = true;
    const fetchHistoricalData = async () => {
      try {
        const url = marketMode === "CRYPTO" 
          ? `https://api.binance.com/api/v3/klines?symbol=${chartSymbol}&interval=${chartInterval}&limit=150`
          : `/api/yahoo?symbol=${chartSymbol}&interval=${chartInterval}`;

        const response = await fetch(url);
        const data = await response.json();
        
        if (!isMounted) return;

        const formattedData = data.map((d: any) => ({
          time: Math.floor(d[0] / 1000), // ms to s
          open: parseFloat(d[1]),
          high: parseFloat(d[2]),
          low: parseFloat(d[3]),
          close: parseFloat(d[4]),
        }));

        const closes = formattedData.map((d: any) => d.close);
        const times = formattedData.map((d: any) => d.time);
        
        closesRef.current = closes;
        timesRef.current = times;
        
        if (times.length > 0) {
          lastTimeRef.current = times[times.length - 1];
        }

        const smaDataPoints = calculateSMA(closes, 20);
        const formattedSmaData = smaDataPoints.map((val, index) => ({
          time: times[index + 19], // offset by period - 1
          value: val,
        }));

        if (seriesRef.current) {
          seriesRef.current.setData(formattedData);
        }
        if (smaSeriesRef.current && formattedSmaData.length > 0) {
          smaSeriesRef.current.setData(formattedSmaData);
        }
        
        setIsLoading(false);
      } catch (err) {
        console.error("Error fetching historical klines", err);
        if (isMounted) setIsLoading(false);
      }
    };

    fetchHistoricalData();

    return () => {
      isMounted = false;
    };
  }, [chartSymbol, chartInterval, marketMode]); // Re-run when symbol, interval, or market changes

  // Update chart on new realtime data
  useEffect(() => {
    if (seriesRef.current && smaSeriesRef.current && latestCandle && !isLoading) {
      const candleTime = latestCandle.time as number;
      
      // Safety check to prevent "Cannot update oldest data" crash
      // Ignore stale websocket ticks from the previous symbol
      if (lastTimeRef.current > 0 && candleTime < lastTimeRef.current) {
        return; 
      }

      // Update main series
      seriesRef.current.update(latestCandle as any);

      // Update SMA
      if (candleTime > lastTimeRef.current) {
        // New candle opened, push it to history
        closesRef.current.push(latestCandle.close);
        timesRef.current.push(candleTime);
        lastTimeRef.current = candleTime;
      } else {
        // Updating current candle
        closesRef.current[closesRef.current.length - 1] = latestCandle.close;
      }

      // Calculate the new SMA value for the last point
      if (closesRef.current.length >= 20) {
        const last20 = closesRef.current.slice(-20);
        const sum = last20.reduce((acc, val) => acc + val, 0);
        const smaValue = sum / 20;

        smaSeriesRef.current.update({
          time: candleTime as any,
          value: smaValue,
        });
      }
    }
  }, [latestCandle, isLoading]);

  return (
    <div className="w-full h-full relative flex flex-col">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-4 px-2 space-y-4 md:space-y-0 z-10">
        
        {/* Title & Status */}
        <div className="flex items-center">
          <h3 className="font-orbitron font-bold text-[#00F0FF] tracking-wider text-sm flex items-center">
            {marketMode === "CRYPTO" ? "QUANTUM MATRIX" : "EQUITIES MATRIX"}
          </h3>
          <div className="flex items-center space-x-2 ml-4">
            {isLoading ? (
              <span className="font-mono text-[9px] text-[#FF5500] animate-pulse">LOADING ARCHIVES...</span>
            ) : (
              <>
                <span className="font-mono text-[9px] text-[rgba(255,255,255,0.4)]">LIVE STREAM</span>
                <div className="w-2 h-2 bg-[#00FF66] rounded-full shadow-[0_0_8px_#00FF66] animate-pulse" />
              </>
            )}
          </div>
        </div>

        {/* Matrix Selectors */}
        <div className="flex space-x-2 font-mono text-xs">
          <div className="flex items-center mr-2 px-2 bg-[rgba(224,36,255,0.1)] border border-[rgba(224,36,255,0.3)] rounded text-[9px] text-[#E024FF]">
            SMA 20
          </div>
          
          <select 
            value={chartSymbol}
            onChange={(e) => setChartSymbol(e.target.value)}
            className="bg-[rgba(0,240,255,0.05)] border border-[rgba(0,240,255,0.2)] text-white px-3 py-1 rounded outline-none focus:border-[#00F0FF] transition-colors cursor-pointer appearance-none"
          >
            {currentSymbols.map(sym => (
              <option key={sym} value={sym} className="bg-[#05050A] text-white">
                {sym.replace("USDT", "")}{marketMode === "CRYPTO" ? "/USDT" : ""}
              </option>
            ))}
          </select>

          <div className="flex bg-[rgba(255,255,255,0.05)] rounded border border-[rgba(255,255,255,0.1)] p-0.5">
            {INTERVALS.map((int) => (
              <button
                key={int.value}
                onClick={() => setChartInterval(int.value)}
                className={`px-2 py-0.5 rounded transition-all duration-200 ${
                  chartInterval === int.value 
                    ? "bg-[rgba(0,240,255,0.2)] text-[#00F0FF] font-bold" 
                    : "text-[rgba(255,255,255,0.4)] hover:text-white"
                }`}
              >
                {int.label}
              </button>
            ))}
          </div>
        </div>

      </div>
      
      {/* Chart Container */}
      <div 
        ref={chartContainerRef} 
        className="flex-1 w-full rounded overflow-hidden" 
        style={{ position: "relative" }}
      />
    </div>
  );
}
