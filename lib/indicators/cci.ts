/**
 * Commodity Channel Index (CCI) indicator.
 * Measures the current price level relative to an average over a given period.
 *   TP = (High + Low + Close) / 3
 *   CCI = (TP - SMA(TP, period)) / (0.015 × Mean Deviation)
 * Pure calculation — no side effects.
 *
 * @param candles - Array of OHLC candle data.
 * @param period  - Look-back period (default 20).
 * @returns Array of CCI values aligned to input indices, with leading nulls.
 */
export function calculateCCI(
  candles: { high: number; low: number; close: number }[],
  period: number = 20
): (number | null)[] {
  if (period <= 0 || candles.length === 0) return [];

  const len = candles.length;

  if (len < period) {
    return new Array(len).fill(null);
  }

  const result: (number | null)[] = [];

  // Pre-calculate Typical Prices
  const tp: number[] = candles.map(
    (c) => (c.high + c.low + c.close) / 3
  );

  for (let i = 0; i < period - 1; i++) {
    result.push(null);
  }

  for (let i = period - 1; i < len; i++) {
    // SMA of Typical Price
    let tpSum = 0;
    for (let j = i - period + 1; j <= i; j++) {
      tpSum += tp[j];
    }
    const smaTP = tpSum / period;

    // Mean Deviation
    let mdSum = 0;
    for (let j = i - period + 1; j <= i; j++) {
      mdSum += Math.abs(tp[j] - smaTP);
    }
    const meanDev = mdSum / period;

    // CCI
    if (meanDev === 0) {
      result.push(0);
    } else {
      result.push((tp[i] - smaTP) / (0.015 * meanDev));
    }
  }

  return result;
}
