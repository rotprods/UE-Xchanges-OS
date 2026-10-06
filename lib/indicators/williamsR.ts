/**
 * Williams %R indicator.
 * Momentum oscillator that reflects the level of the close relative to
 * the highest high over a look-back period. Bounded between 0 and -100.
 *   %R = (Highest High - Close) / (Highest High - Lowest Low) × -100
 * Pure calculation — no side effects.
 *
 * @param candles - Array of OHLC candle data.
 * @param period  - Look-back period (default 14).
 * @returns Array of Williams %R values aligned to input indices,
 *          with leading nulls for the warm-up window.
 */
export function calculateWilliamsR(
  candles: { high: number; low: number; close: number }[],
  period: number = 14
): (number | null)[] {
  if (period <= 0 || candles.length === 0) return [];

  const len = candles.length;

  if (len < period) {
    return new Array(len).fill(null);
  }

  const result: (number | null)[] = [];

  for (let i = 0; i < period - 1; i++) {
    result.push(null);
  }

  for (let i = period - 1; i < len; i++) {
    let highestHigh = -Infinity;
    let lowestLow = Infinity;

    for (let j = i - period + 1; j <= i; j++) {
      if (candles[j].high > highestHigh) highestHigh = candles[j].high;
      if (candles[j].low < lowestLow) lowestLow = candles[j].low;
    }

    const range = highestHigh - lowestLow;

    if (range === 0) {
      result.push(0);
    } else {
      result.push(((highestHigh - candles[i].close) / range) * -100);
    }
  }

  return result;
}
