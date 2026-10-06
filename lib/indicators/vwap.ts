/**
 * Volume-Weighted Average Price (VWAP) indicator.
 * VWAP = Σ(typicalPrice × volume) / Σ(volume)
 * If volume is missing, defaults to 1.
 * Pure calculation — no side effects.
 */
export function calculateVWAP(
  candles: { high: number; low: number; close: number; volume?: number }[]
): (number | null)[] {
  if (candles.length === 0) return [];

  const result: (number | null)[] = [];
  let cumulativeTPV = 0; // cumulative (typicalPrice × volume)
  let cumulativeVolume = 0;

  for (let i = 0; i < candles.length; i++) {
    const { high, low, close } = candles[i];
    const volume = candles[i].volume ?? 1;
    const typicalPrice = (high + low + close) / 3;

    cumulativeTPV += typicalPrice * volume;
    cumulativeVolume += volume;

    if (cumulativeVolume === 0) {
      result.push(null);
    } else {
      result.push(cumulativeTPV / cumulativeVolume);
    }
  }

  return result;
}
