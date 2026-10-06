/**
 * Simple Moving Average (SMA) indicator.
 * Pure calculation — no side effects.
 */
export function calculateSMA(
  candles: { close: number }[],
  period: number
): (number | null)[] {
  if (period <= 0 || candles.length === 0) return [];

  const result: (number | null)[] = [];

  for (let i = 0; i < candles.length; i++) {
    if (i < period - 1) {
      result.push(null);
      continue;
    }

    let sum = 0;
    for (let j = i - period + 1; j <= i; j++) {
      sum += candles[j].close;
    }
    result.push(sum / period);
  }

  return result;
}
