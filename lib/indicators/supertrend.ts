/**
 * SuperTrend indicator.
 * Trend-following overlay that uses ATR-based upper/lower bands to determine
 * trend direction. When price closes above the upper band the trend flips up;
 * when it closes below the lower band the trend flips down.
 * Pure calculation — no side effects.
 *
 * @param candles    - Array of OHLC candle data.
 * @param period     - ATR period (default 10).
 * @param multiplier - ATR multiplier for band distance (default 3).
 * @returns Object with `supertrend` values and `direction` (1 = up, -1 = down),
 *          aligned to input indices with leading nulls for the warm-up window.
 */
export function calculateSuperTrend(
  candles: { high: number; low: number; close: number }[],
  period: number = 10,
  multiplier: number = 3
): { supertrend: (number | null)[]; direction: (1 | -1 | null)[] } {
  const len = candles.length;

  if (period <= 0 || len === 0) {
    return { supertrend: [], direction: [] };
  }

  if (len < period + 1) {
    return {
      supertrend: new Array(len).fill(null),
      direction: new Array(len).fill(null),
    };
  }

  // --- Step 1: Calculate True Range and ATR (SMA-based) ---
  const tr: number[] = [0];
  for (let i = 1; i < len; i++) {
    const highLow = candles[i].high - candles[i].low;
    const highPrevClose = Math.abs(candles[i].high - candles[i - 1].close);
    const lowPrevClose = Math.abs(candles[i].low - candles[i - 1].close);
    tr.push(Math.max(highLow, highPrevClose, lowPrevClose));
  }

  // ATR using SMA, first valid at index = period
  const atr: (number | null)[] = new Array(period).fill(null);
  let trSum = 0;
  for (let i = 1; i <= period; i++) {
    trSum += tr[i];
  }
  atr.push(trSum / period);

  for (let i = period + 1; i < len; i++) {
    trSum = trSum - tr[i - period] + tr[i];
    atr.push(trSum / period);
  }

  // --- Step 2: Calculate SuperTrend ---
  const supertrend: (number | null)[] = new Array(len).fill(null);
  const direction: (1 | -1 | null)[] = new Array(len).fill(null);

  // First valid index
  const start = period;
  const hl2 = (candles[start].high + candles[start].low) / 2;
  const atrVal = atr[start] as number;

  let prevUpperBand = hl2 + multiplier * atrVal;
  let prevLowerBand = hl2 - multiplier * atrVal;
  let prevDir: 1 | -1 = candles[start].close > prevUpperBand ? 1 : -1;

  supertrend[start] = prevDir === 1 ? prevLowerBand : prevUpperBand;
  direction[start] = prevDir;

  for (let i = start + 1; i < len; i++) {
    const currentATR = atr[i] as number;
    const mid = (candles[i].high + candles[i].low) / 2;

    let upperBand = mid + multiplier * currentATR;
    let lowerBand = mid - multiplier * currentATR;

    // Carry forward tighter bands
    if (lowerBand < prevLowerBand && candles[i - 1].close > prevLowerBand) {
      // Don't let the lower band decrease when in up-trend
    } else if (lowerBand > prevLowerBand) {
      // Lower band moved up — keep it
    } else {
      lowerBand = prevLowerBand;
    }

    if (upperBand > prevUpperBand && candles[i - 1].close < prevUpperBand) {
      // Don't let the upper band increase when in down-trend
    } else if (upperBand < prevUpperBand) {
      // Upper band moved down — keep it
    } else {
      upperBand = prevUpperBand;
    }

    // Determine direction
    let dir: 1 | -1;
    if (prevDir === -1 && candles[i].close > prevUpperBand) {
      dir = 1;
    } else if (prevDir === 1 && candles[i].close < prevLowerBand) {
      dir = -1;
    } else {
      dir = prevDir;
    }

    supertrend[i] = dir === 1 ? lowerBand : upperBand;
    direction[i] = dir;

    prevUpperBand = upperBand;
    prevLowerBand = lowerBand;
    prevDir = dir;
  }

  return { supertrend, direction };
}
