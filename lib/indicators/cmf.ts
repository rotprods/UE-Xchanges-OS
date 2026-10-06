/**
 * Chaikin Money Flow (CMF) indicator.
 * Volume-weighted accumulation/distribution measure bounded between -1 and +1.
 *   MF Multiplier = ((Close - Low) - (High - Close)) / (High - Low)
 *   MF Volume     = MF Multiplier × Volume
 *   CMF           = Σ(MF Volume, period) / Σ(Volume, period)
 * Pure calculation — no side effects.
 *
 * @param candles - Array of OHLC candle data with optional volume.
 *                  If volume is omitted it defaults to 0 for that bar.
 * @param period  - Look-back period (default 20).
 * @returns Array of CMF values aligned to input indices, with leading nulls.
 */
export function calculateCMF(
  candles: { high: number; low: number; close: number; volume?: number }[],
  period: number = 20
): (number | null)[] {
  if (period <= 0 || candles.length === 0) return [];

  const len = candles.length;

  if (len < period) {
    return new Array(len).fill(null);
  }

  // Pre-calculate Money Flow Volume for each bar
  const mfVolume: number[] = [];
  const volumes: number[] = [];

  for (let i = 0; i < len; i++) {
    const vol = candles[i].volume ?? 0;
    const range = candles[i].high - candles[i].low;

    let mfMultiplier: number;
    if (range === 0) {
      mfMultiplier = 0;
    } else {
      mfMultiplier =
        ((candles[i].close - candles[i].low) - (candles[i].high - candles[i].close)) / range;
    }

    mfVolume.push(mfMultiplier * vol);
    volumes.push(vol);
  }

  const result: (number | null)[] = [];

  for (let i = 0; i < period - 1; i++) {
    result.push(null);
  }

  // Initial sums for first window
  let mfvSum = 0;
  let volSum = 0;
  for (let i = 0; i < period; i++) {
    mfvSum += mfVolume[i];
    volSum += volumes[i];
  }

  result.push(volSum === 0 ? 0 : mfvSum / volSum);

  // Sliding window
  for (let i = period; i < len; i++) {
    mfvSum = mfvSum - mfVolume[i - period] + mfVolume[i];
    volSum = volSum - volumes[i - period] + volumes[i];
    result.push(volSum === 0 ? 0 : mfvSum / volSum);
  }

  return result;
}
