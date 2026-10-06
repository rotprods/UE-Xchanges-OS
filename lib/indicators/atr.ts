/**
 * Average True Range (ATR) indicator.
 * Measures market volatility using the True Range:
 *   TR = max(high - low, |high - prevClose|, |low - prevClose|).
 * ATR is the Simple Moving Average of TR over `period` bars.
 * Pure calculation — no side effects.
 *
 * @param candles - Array of OHLC candle data.
 * @param period  - Averaging period (default 14).
 * @returns Array of ATR values aligned to input indices, with leading nulls
 *          for the warm-up window (`period` candles required).
 */
export function calculateATR(
  candles: { high: number; low: number; close: number }[],
  period: number = 14
): (number | null)[] {
  if (period <= 0 || candles.length === 0) return [];

  const len = candles.length;

  if (len < period + 1) {
    return new Array(len).fill(null);
  }

  const result: (number | null)[] = [];

  // --- Step 1: Calculate True Range for each bar starting at index 1 ---
  const tr: number[] = [0]; // Index 0 has no previous close; TR is 0

  for (let i = 1; i < len; i++) {
    const highLow = candles[i].high - candles[i].low;
    const highPrevClose = Math.abs(candles[i].high - candles[i - 1].close);
    const lowPrevClose = Math.abs(candles[i].low - candles[i - 1].close);
    tr.push(Math.max(highLow, highPrevClose, lowPrevClose));
  }

  // --- Step 2: ATR = SMA of TR ---
  // We skip tr[0] (no valid TR) and start the window at tr[1..period]
  // So the first ATR appears at candle index = period.
  for (let i = 0; i < period; i++) {
    result.push(null);
  }

  // First ATR: average of TR[1..period]
  let trSum = 0;
  for (let i = 1; i <= period; i++) {
    trSum += tr[i];
  }
  result.push(trSum / period);

  // Subsequent ATR values using rolling SMA
  for (let i = period + 1; i < len; i++) {
    trSum = trSum - tr[i - period] + tr[i];
    result.push(trSum / period);
  }

  return result;
}
