import { calculateEMA } from "./ema";

/**
 * Moving Average Convergence Divergence (MACD) indicator.
 * MACD line = fastEMA − slowEMA
 * Signal line = EMA of MACD line
 * Histogram = MACD − Signal
 * Pure calculation — no side effects.
 */
export function calculateMACD(
  candles: { close: number }[],
  fastPeriod: number = 12,
  slowPeriod: number = 26,
  signalPeriod: number = 9
): {
  macd: (number | null)[];
  signal: (number | null)[];
  histogram: (number | null)[];
} {
  if (candles.length === 0) {
    return { macd: [], signal: [], histogram: [] };
  }

  const fastEMA = calculateEMA(candles, fastPeriod);
  const slowEMA = calculateEMA(candles, slowPeriod);

  // MACD line: fastEMA - slowEMA (null until both EMAs are available)
  const macdLine: (number | null)[] = [];
  for (let i = 0; i < candles.length; i++) {
    const fast = fastEMA[i];
    const slow = slowEMA[i];
    if (fast !== null && slow !== null) {
      macdLine.push(fast - slow);
    } else {
      macdLine.push(null);
    }
  }

  // Signal line: EMA of the non-null MACD values, mapped back to original indices
  const nonNullMacdValues: { close: number }[] = [];
  const nonNullIndices: number[] = [];
  for (let i = 0; i < macdLine.length; i++) {
    if (macdLine[i] !== null) {
      nonNullMacdValues.push({ close: macdLine[i] as number });
      nonNullIndices.push(i);
    }
  }

  const signalEMA = calculateEMA(nonNullMacdValues, signalPeriod);

  // Map signal values back to original indices
  const signalLine: (number | null)[] = new Array(candles.length).fill(null);
  for (let i = 0; i < nonNullIndices.length; i++) {
    signalLine[nonNullIndices[i]] = signalEMA[i];
  }

  // Histogram: MACD - Signal
  const histogram: (number | null)[] = [];
  for (let i = 0; i < candles.length; i++) {
    const m = macdLine[i];
    const s = signalLine[i];
    if (m !== null && s !== null) {
      histogram.push(m - s);
    } else {
      histogram.push(null);
    }
  }

  return { macd: macdLine, signal: signalLine, histogram };
}
