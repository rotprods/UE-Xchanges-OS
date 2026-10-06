import { calculateSMA } from "./sma";

/**
 * Bollinger Bands indicator.
 * Middle band = SMA(period)
 * Upper band  = SMA + (stdDevMultiplier × σ)
 * Lower band  = SMA − (stdDevMultiplier × σ)
 * Pure calculation — no side effects.
 */
export function calculateBollingerBands(
  candles: { close: number }[],
  period: number = 20,
  stdDevMultiplier: number = 2
): {
  upper: (number | null)[];
  middle: (number | null)[];
  lower: (number | null)[];
} {
  if (candles.length === 0) {
    return { upper: [], middle: [], lower: [] };
  }

  const sma = calculateSMA(candles, period);

  const upper: (number | null)[] = [];
  const middle: (number | null)[] = [];
  const lower: (number | null)[] = [];

  for (let i = 0; i < candles.length; i++) {
    const smaValue = sma[i];

    if (smaValue === null) {
      upper.push(null);
      middle.push(null);
      lower.push(null);
      continue;
    }

    // Calculate standard deviation over the window
    let sumSquaredDiff = 0;
    for (let j = i - period + 1; j <= i; j++) {
      const diff = candles[j].close - smaValue;
      sumSquaredDiff += diff * diff;
    }
    const stdDev = Math.sqrt(sumSquaredDiff / period);

    middle.push(smaValue);
    upper.push(smaValue + stdDevMultiplier * stdDev);
    lower.push(smaValue - stdDevMultiplier * stdDev);
  }

  return { upper, middle, lower };
}
