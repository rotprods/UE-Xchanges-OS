/**
 * SnapshotBuilder — Captures a complete market snapshot for AI training.
 * 
 * Called every 5 minutes by the cron endpoint. Each snapshot captures:
 * - Current price, OHLCV data
 * - All technical indicators (RSI, MACD, BB, SMA, EMA, VWAP, etc.)
 * - Trend analysis
 * - On-chain metrics (mempool fees, whale count)
 * - Derivatives data (funding rate, OI, liquidations)
 * - Sentiment (Fear & Greed)
 * - Macro data (DeFi TVL, BTC dominance)
 * - Graph Engine output (signal score, confidence, direction)
 */

import { calculateSMA } from "../indicators/sma";
import { calculateEMA } from "../indicators/ema";
import { calculateRSI } from "../indicators/rsi";
import { calculateMACD } from "../indicators/macd";
import { calculateBollingerBands } from "../indicators/bollingerBands";
import { calculateVWAP } from "../indicators/vwap";
import { calculateADX } from "../indicators/adx";
import { calculateOBV } from "../indicators/obv";
import { calculateATR } from "../indicators/atr";

export interface MarketSnapshotData {
  timestamp: number;
  symbol: string;
  price: number;
  open: number;
  high: number;
  low: number;
  volume24h: number;
  // Technical
  rsi14: number | null;
  sma7: number | null;
  sma25: number | null;
  sma99: number | null;
  ema21: number | null;
  macdLine: number | null;
  macdSignal: number | null;
  macdHistogram: number | null;
  bbUpper: number | null;
  bbLower: number | null;
  bbWidth: number | null;
  vwap: number | null;
  adx: number | null;
  obv: number | null;
  atr14: number | null;
  // Trend
  trendDirection: string | null;
  trendStrength: number | null;
  // On-chain
  btcMempoolFee: number | null;
  ethGasGwei: number | null;
  whaleCount1h: number | null;
  liquidationVolume1h: number | null;
  // Derivatives
  fundingRate: number | null;
  openInterest: number | null;
  longShortRatio: number | null;
  putCallRatio: number | null;
  // Sentiment
  fearGreedIndex: number | null;
  // Macro
  defiTvl: number | null;
  btcDominance: number | null;
  // Graph
  graphSignalScore: number | null;
  graphConfidence: number | null;
  graphDirection: string | null;
}

interface CandleRaw {
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

/**
 * Fetches recent klines from Binance and computes all indicators.
 */
export async function buildSnapshot(symbol: string): Promise<MarketSnapshotData> {
  const now = Date.now();

  // Fetch 200 recent 5-minute klines for indicator computation
  const candles = await fetchKlines(symbol, "5m", 200);
  const closes = candles.map((c) => c.close);
  const latestCandle = candles[candles.length - 1];

  // ─── Technical Indicators ───────────────────────────────────────
  const rsiValues = calculateRSI(candles, 14);
  const sma7 = calculateSMA(candles, 7);
  const sma25 = calculateSMA(candles, 25);
  const sma99 = calculateSMA(candles, 99);
  const ema21 = calculateEMA(candles, 21);
  const macd = calculateMACD(candles);
  const bb = calculateBollingerBands(candles, 20, 2);

  const lastRsi = rsiValues.length > 0 ? rsiValues[rsiValues.length - 1] : null;
  const lastSma7 = sma7.length > 0 ? sma7[sma7.length - 1] : null;
  const lastSma25 = sma25.length > 0 ? sma25[sma25.length - 1] : null;
  const lastSma99 = sma99.length > 0 ? sma99[sma99.length - 1] : null;
  const lastEma21 = ema21.length > 0 ? ema21[ema21.length - 1] : null;
  const lastMacdLine = macd.macd.length > 0 ? macd.macd[macd.macd.length - 1] : null;
  const lastMacdSignal = macd.signal.length > 0 ? macd.signal[macd.signal.length - 1] : null;
  const lastMacdHist = macd.histogram.length > 0 ? macd.histogram[macd.histogram.length - 1] : null;
  const lastBbUpper = bb.upper.length > 0 ? bb.upper[bb.upper.length - 1] : null;
  const lastBbLower = bb.lower.length > 0 ? bb.lower[bb.lower.length - 1] : null;
  const lastBbMiddle = bb.middle.length > 0 ? bb.middle[bb.middle.length - 1] : null;
  const bbWidth = lastBbUpper != null && lastBbLower != null && lastBbMiddle != null && lastBbMiddle !== 0
    ? (lastBbUpper - lastBbLower) / lastBbMiddle
    : null;

  // ─── Trend Direction ────────────────────────────────────────────
  let trendDirection: string | null = null;
  let trendStrength: number | null = null;
  if (lastSma7 !== null && lastSma25 !== null && lastSma99 !== null) {
    if (lastSma7 > lastSma25 && lastSma25 > lastSma99) {
      trendDirection = "STRONG_BULL";
      trendStrength = Math.min(100, ((lastSma7 - lastSma99) / lastSma99) * 1000);
    } else if (lastSma7 > lastSma25) {
      trendDirection = "BULL";
      trendStrength = Math.min(100, ((lastSma7 - lastSma25) / lastSma25) * 1000);
    } else if (lastSma7 < lastSma25 && lastSma25 < lastSma99) {
      trendDirection = "STRONG_BEAR";
      trendStrength = Math.min(100, ((lastSma99 - lastSma7) / lastSma7) * 1000);
    } else if (lastSma7 < lastSma25) {
      trendDirection = "BEAR";
      trendStrength = Math.min(100, ((lastSma25 - lastSma7) / lastSma7) * 1000);
    } else {
      trendDirection = "NEUTRAL";
      trendStrength = 0;
    }
  }

  // ─── External Data (fetched in parallel) ────────────────────────
  const [mempoolFee, fearGreed, fundingData, defiData] = await Promise.all([
    fetchMempoolFee(),
    fetchFearGreed(),
    fetchFundingRate(symbol),
    fetchDefiTvl(),
  ]);

  // ─── VWAP ───────────────────────────────────────────────────────
  const vwapCandles = candles.map((c) => ({
    high: c.high,
    low: c.low,
    close: c.close,
    volume: c.volume,
  }));
  const vwapValues = calculateVWAP(vwapCandles);
  const lastVwap = vwapValues.length > 0 ? vwapValues[vwapValues.length - 1] : null;

  return {
    timestamp: now,
    symbol,
    price: latestCandle.close,
    open: latestCandle.open,
    high: latestCandle.high,
    low: latestCandle.low,
    volume24h: candles.reduce((sum, c) => sum + c.volume, 0),
    rsi14: lastRsi,
    sma7: lastSma7,
    sma25: lastSma25,
    sma99: lastSma99,
    ema21: lastEma21,
    macdLine: lastMacdLine,
    macdSignal: lastMacdSignal,
    macdHistogram: lastMacdHist,
    bbUpper: lastBbUpper,
    bbLower: lastBbLower,
    bbWidth,
    vwap: lastVwap,
    adx: (() => { const v = calculateADX(candles, 14); return v.length > 0 ? v[v.length - 1] : null; })(),
    obv: (() => { const v = calculateOBV(candles); return v.length > 0 ? v[v.length - 1] : null; })(),
    atr14: (() => { const v = calculateATR(candles, 14); return v.length > 0 ? v[v.length - 1] : null; })(),
    trendDirection,
    trendStrength,
    btcMempoolFee: mempoolFee,
    ethGasGwei: null, // Add later
    whaleCount1h: null, // Tracked in-memory via store
    liquidationVolume1h: null,
    fundingRate: fundingData?.rate ?? null,
    openInterest: fundingData?.oi ?? null,
    longShortRatio: null,
    putCallRatio: null,
    fearGreedIndex: fearGreed,
    defiTvl: defiData?.tvl ?? null,
    btcDominance: null,
    graphSignalScore: null, // Filled by GraphEngine
    graphConfidence: null,
    graphDirection: null,
  };
}

// ─── Data Fetchers ────────────────────────────────────────────────────────────

async function fetchKlines(
  symbol: string,
  interval: string,
  limit: number
): Promise<CandleRaw[]> {
  try {
    const url = `https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=${interval}&limit=${limit}`;
    const res = await fetch(url);
    if (!res.ok) return [];
    const data: any[] = await res.json();
    return data.map((k: any) => ({
      open: parseFloat(k[1]),
      high: parseFloat(k[2]),
      low: parseFloat(k[3]),
      close: parseFloat(k[4]),
      volume: parseFloat(k[5]),
    }));
  } catch {
    return [];
  }
}

async function fetchMempoolFee(): Promise<number | null> {
  try {
    const res = await fetch("https://mempool.space/api/v1/fees/recommended");
    if (!res.ok) return null;
    const data = await res.json();
    return data.fastestFee ?? null;
  } catch {
    return null;
  }
}

async function fetchFearGreed(): Promise<number | null> {
  try {
    const res = await fetch("https://api.alternative.me/fng/?limit=1");
    if (!res.ok) return null;
    const data = await res.json();
    return data.data?.[0]?.value ? parseInt(data.data[0].value) : null;
  } catch {
    return null;
  }
}

async function fetchFundingRate(
  symbol: string
): Promise<{ rate: number; oi: number } | null> {
  try {
    const [fundingRes, oiRes] = await Promise.all([
      fetch(
        `https://fapi.binance.com/fapi/v1/fundingRate?symbol=${symbol}&limit=1`
      ),
      fetch(`https://fapi.binance.com/fapi/v1/openInterest?symbol=${symbol}`),
    ]);
    if (!fundingRes.ok || !oiRes.ok) return null;
    const fundingData = await fundingRes.json();
    const oiData = await oiRes.json();
    return {
      rate: parseFloat(fundingData[0]?.fundingRate ?? "0"),
      oi: parseFloat(oiData.openInterest ?? "0"),
    };
  } catch {
    return null;
  }
}

async function fetchDefiTvl(): Promise<{ tvl: number } | null> {
  try {
    const res = await fetch("https://api.llama.fi/v2/protocols");
    if (!res.ok) return null;
    const data: any[] = await res.json();
    const totalTvl = data.reduce(
      (sum: number, p: any) => sum + (p.tvl ?? 0),
      0
    );
    return { tvl: totalTvl };
  } catch {
    return null;
  }
}
