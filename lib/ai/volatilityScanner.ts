/**
 * Volatility Scanner
 * Uses Bollinger Bands width to classify market volatility state and
 * estimate breakout probability.
 * Pure calculation — no side effects.
 */

import { calculateBollingerBands } from "../indicators/bollingerBands";

export type VolatilityState = "SQUEEZE" | "EXPANSION" | "NORMAL";

export interface VolatilityResult {
  state: VolatilityState;
  width: number; // BB width normalised by middle band
  breakoutProbability: number; // 0–1
  signal: string; // human-readable summary
}

interface Candle {
  open: number;
  high: number;
  low: number;
  close: number;
}

// Thresholds (normalized BB width)
const SQUEEZE_THRESHOLD = 0.05;
const EXPANSION_THRESHOLD = 0.15;

// ─── Helpers ─────────────────────────────────────────────────────────────────

function lastNonNull(arr: (number | null)[]): number | null {
  for (let i = arr.length - 1; i >= 0; i--) {
    if (arr[i] !== null) return arr[i] as number;
  }
  return null;
}

// ─── Main Export ─────────────────────────────────────────────────────────────

/**
 * Scan volatility using Bollinger Bands (period=20, multiplier=2).
 *
 * @param candles - Array of OHLC candles (needs ≥20 for accuracy)
 */
export function scanVolatility(candles: Candle[]): VolatilityResult {
  if (candles.length < 5) {
    return {
      state: "NORMAL",
      width: 0,
      breakoutProbability: 0,
      signal: "Insufficient data for volatility analysis.",
    };
  }

  const bb = calculateBollingerBands(candles, 20, 2);
  const upper = lastNonNull(bb.upper);
  const middle = lastNonNull(bb.middle);
  const lower = lastNonNull(bb.lower);

  if (upper === null || middle === null || lower === null || middle === 0) {
    return {
      state: "NORMAL",
      width: 0,
      breakoutProbability: 0,
      signal: "Calculating Bollinger Bands…",
    };
  }

  const width = (upper - lower) / middle;

  // ─── State classification ─────────────────────────────────────────────────
  let state: VolatilityState;
  let breakoutProbability: number;
  let signal: string;

  if (width < SQUEEZE_THRESHOLD) {
    state = "SQUEEZE";
    // Tighter squeeze → higher breakout probability
    breakoutProbability = parseFloat(
      Math.min(1, 0.6 + ((SQUEEZE_THRESHOLD - width) / SQUEEZE_THRESHOLD) * 0.4).toFixed(3)
    );
    signal = `Bollinger Bands in SQUEEZE (width ${(width * 100).toFixed(2)}%). Coiling price action — high-probability breakout imminent.`;
  } else if (width > EXPANSION_THRESHOLD) {
    state = "EXPANSION";
    // Already expanding — breakout in progress, diminishing setup probability
    breakoutProbability = parseFloat(
      Math.max(0.1, 1 - ((width - EXPANSION_THRESHOLD) / 0.3)).toFixed(3)
    );
    signal = `Bollinger Bands EXPANDING (width ${(width * 100).toFixed(2)}%). High volatility regime active — trend continuation likely.`;
  } else {
    state = "NORMAL";
    // Linear interpolation between thresholds
    const normPos = (width - SQUEEZE_THRESHOLD) / (EXPANSION_THRESHOLD - SQUEEZE_THRESHOLD);
    breakoutProbability = parseFloat((0.3 + normPos * 0.3).toFixed(3));
    signal = `Bollinger Bands in normal range (width ${(width * 100).toFixed(2)}%). Watching for compression or expansion signals.`;
  }

  return { state, width: parseFloat(width.toFixed(5)), breakoutProbability, signal };
}
