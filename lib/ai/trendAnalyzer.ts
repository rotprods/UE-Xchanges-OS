/**
 * Trend Analyzer
 * Uses SMA crossover logic to determine market trend direction and strength.
 * Pure calculation — no side effects.
 */

import { calculateSMA } from "../indicators/sma";

export type TrendDirection =
  | "STRONG_BULL"
  | "BULL"
  | "NEUTRAL"
  | "BEAR"
  | "STRONG_BEAR";

export type SmaCrossSignal = "GOLDEN" | "DEATH" | "NONE";

export interface TrendResult {
  direction: TrendDirection;
  strength: number; // 0–100
  signal: string; // human-readable summary
  smaCross: SmaCrossSignal;
}

interface Candle {
  open: number;
  high: number;
  low: number;
  close: number;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

/** Returns the last non-null value from an array, or null. */
function lastValue(arr: (number | null)[]): number | null {
  for (let i = arr.length - 1; i >= 0; i--) {
    if (arr[i] !== null) return arr[i] as number;
  }
  return null;
}

/** Returns the second-to-last non-null value, or null. */
function prevValue(arr: (number | null)[]): number | null {
  let count = 0;
  for (let i = arr.length - 1; i >= 0; i--) {
    if (arr[i] !== null) {
      count++;
      if (count === 2) return arr[i] as number;
    }
  }
  return null;
}

// ─── Main Export ─────────────────────────────────────────────────────────────

/**
 * Analyze the trend using SMA7, SMA25, and SMA99 crossovers.
 *
 * @param candles - Array of OHLC candles (needs at least 99 for full accuracy)
 */
export function analyzeTrend(candles: Candle[]): TrendResult {
  if (candles.length < 10) {
    return {
      direction: "NEUTRAL",
      strength: 0,
      signal: "Insufficient data for trend analysis.",
      smaCross: "NONE",
    };
  }

  const sma7 = calculateSMA(candles, 7);
  const sma25 = calculateSMA(candles, 25);
  const sma99 = calculateSMA(candles, 99);

  const s7 = lastValue(sma7);
  const s25 = lastValue(sma25);
  const s99 = lastValue(sma99);

  const prevS7 = prevValue(sma7);
  const prevS25 = prevValue(sma25);

  // ─── SMA cross detection ──────────────────────────────────────────────────
  let smaCross: SmaCrossSignal = "NONE";
  if (s7 !== null && s25 !== null && prevS7 !== null && prevS25 !== null) {
    if (prevS7 <= prevS25 && s7 > s25) smaCross = "GOLDEN";
    else if (prevS7 >= prevS25 && s7 < s25) smaCross = "DEATH";
  }

  // ─── Direction & strength ─────────────────────────────────────────────────
  const closePrice = candles[candles.length - 1].close;

  // Score: +1 for each SMA the price is above
  let bullScore = 0;
  let totalSmas = 0;

  if (s7 !== null) { totalSmas++; if (closePrice > s7) bullScore++; }
  if (s25 !== null) { totalSmas++; if (closePrice > s25) bullScore++; }
  if (s99 !== null) { totalSmas++; if (closePrice > s99) bullScore++; }

  // Alignment: SMA7 > SMA25 > SMA99 (fully aligned bull)
  let alignmentScore = 0;
  if (s7 !== null && s25 !== null && s7 > s25) alignmentScore++;
  if (s25 !== null && s99 !== null && s25 > s99) alignmentScore++;
  if (s7 !== null && s99 !== null && s7 > s99) alignmentScore++;

  const scoreFraction = totalSmas > 0 ? bullScore / totalSmas : 0.5;
  const alignFraction = alignmentScore / 3;

  // Combined 0→1 where 0.5 = neutral
  const combined = (scoreFraction * 0.6 + alignFraction * 0.4);

  let direction: TrendDirection;
  let strength: number;

  if (combined >= 0.85) {
    direction = "STRONG_BULL";
    strength = Math.round(70 + (combined - 0.85) / 0.15 * 30);
  } else if (combined >= 0.6) {
    direction = "BULL";
    strength = Math.round(50 + (combined - 0.6) / 0.25 * 20);
  } else if (combined >= 0.4) {
    direction = "NEUTRAL";
    strength = Math.round(30 + (combined - 0.4) / 0.2 * 20);
  } else if (combined >= 0.15) {
    direction = "BEAR";
    strength = Math.round(50 + (0.4 - combined) / 0.25 * 20);
  } else {
    direction = "STRONG_BEAR";
    strength = Math.round(70 + (0.15 - combined) / 0.15 * 30);
  }

  strength = Math.max(0, Math.min(100, strength));

  // ─── Human-readable signal ────────────────────────────────────────────────
  let signal: string;
  const crossMsg =
    smaCross === "GOLDEN"
      ? " Golden Cross confirmed — SMA7 crossed above SMA25."
      : smaCross === "DEATH"
      ? " Death Cross confirmed — SMA7 crossed below SMA25."
      : "";

  switch (direction) {
    case "STRONG_BULL":
      signal = `Price above all key SMAs with full bullish alignment.${crossMsg} Strong uptrend in force.`;
      break;
    case "BULL":
      signal = `Price trading above short-term averages.${crossMsg} Moderate bullish momentum.`;
      break;
    case "NEUTRAL":
      signal = `Price oscillating around moving averages.${crossMsg} No clear directional bias.`;
      break;
    case "BEAR":
      signal = `Price below short-term averages.${crossMsg} Moderate bearish pressure.`;
      break;
    case "STRONG_BEAR":
      signal = `Price below all key SMAs with full bearish alignment.${crossMsg} Strong downtrend in force.`;
      break;
  }

  return { direction, strength, signal, smaCross };
}
