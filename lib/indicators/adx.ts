/**
 * Average Directional Index (ADX) indicator.
 * Measures the strength of a trend regardless of direction.
 * Uses Wilder smoothing for +DI, -DI, and DX calculations.
 * Pure calculation — no side effects.
 *
 * @param candles - Array of OHLC candle data.
 * @param period  - Smoothing period (default 14).
 * @returns Array of ADX values aligned to input indices, with leading nulls
 *          for the warm-up window (2 × period - 1 candles required).
 */
export function calculateADX(
  candles: { high: number; low: number; close: number }[],
  period: number = 14
): (number | null)[] {
  if (period <= 0 || candles.length === 0) return [];

  const len = candles.length;
  // Need at least 2*period candles to produce the first ADX value
  if (len < 2 * period) {
    return new Array(len).fill(null);
  }

  const result: (number | null)[] = [];

  // --- Step 1: True Range, +DM, -DM for each bar (starting at index 1) ---
  const tr: number[] = [];
  const plusDM: number[] = [];
  const minusDM: number[] = [];

  for (let i = 1; i < len; i++) {
    const highLow = candles[i].high - candles[i].low;
    const highPrevClose = Math.abs(candles[i].high - candles[i - 1].close);
    const lowPrevClose = Math.abs(candles[i].low - candles[i - 1].close);
    tr.push(Math.max(highLow, highPrevClose, lowPrevClose));

    const upMove = candles[i].high - candles[i - 1].high;
    const downMove = candles[i - 1].low - candles[i].low;

    plusDM.push(upMove > downMove && upMove > 0 ? upMove : 0);
    minusDM.push(downMove > upMove && downMove > 0 ? downMove : 0);
  }

  // --- Step 2: Wilder-smoothed TR, +DM, -DM over first `period` bars ---
  let smoothTR = 0;
  let smoothPlusDM = 0;
  let smoothMinusDM = 0;

  for (let i = 0; i < period; i++) {
    smoothTR += tr[i];
    smoothPlusDM += plusDM[i];
    smoothMinusDM += minusDM[i];
  }

  // --- Step 3: First +DI / -DI / DX at index = period ---
  const dxValues: number[] = [];

  const computeDX = (): number => {
    const pdi = smoothTR === 0 ? 0 : (smoothPlusDM / smoothTR) * 100;
    const mdi = smoothTR === 0 ? 0 : (smoothMinusDM / smoothTR) * 100;
    const diSum = pdi + mdi;
    return diSum === 0 ? 0 : (Math.abs(pdi - mdi) / diSum) * 100;
  };

  dxValues.push(computeDX());

  // Continue Wilder smoothing for remaining bars, collecting DX
  for (let i = period; i < tr.length; i++) {
    smoothTR = smoothTR - smoothTR / period + tr[i];
    smoothPlusDM = smoothPlusDM - smoothPlusDM / period + plusDM[i];
    smoothMinusDM = smoothMinusDM - smoothMinusDM / period + minusDM[i];
    dxValues.push(computeDX());
  }

  // --- Step 4: ADX = Wilder-smoothed DX over `period` ---
  // First ADX is SMA of first `period` DX values
  // Leading nulls: first ADX appears at candle index = 2*period - 1
  const warmUp = 2 * period - 1;

  for (let i = 0; i < warmUp; i++) {
    result.push(null);
  }

  let adxSum = 0;
  for (let i = 0; i < period; i++) {
    adxSum += dxValues[i];
  }
  let adx = adxSum / period;
  result.push(adx);

  // Subsequent ADX with Wilder smoothing
  for (let i = period; i < dxValues.length; i++) {
    adx = (adx * (period - 1) + dxValues[i]) / period;
    result.push(adx);
  }

  return result;
}
