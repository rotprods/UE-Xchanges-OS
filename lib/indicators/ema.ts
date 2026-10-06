/**
 * Exponential Moving Average (EMA) indicator.
 * Pure calculation — no side effects.
 */
export function calculateEMA(
  candles: { close: number }[],
  period: number
): (number | null)[] {
  if (period <= 0 || candles.length === 0) return [];

  const result: (number | null)[] = [];
  const multiplier = 2 / (period + 1);

  // Fill nulls until we have enough data for the initial SMA seed
  for (let i = 0; i < period - 1 && i < candles.length; i++) {
    result.push(null);
  }

  if (candles.length < period) return result;

  // Seed the EMA with the SMA of the first `period` candles
  let sum = 0;
  for (let i = 0; i < period; i++) {
    sum += candles[i].close;
  }
  let ema = sum / period;
  result.push(ema);

  // Calculate remaining EMA values
  for (let i = period; i < candles.length; i++) {
    ema = (candles[i].close - ema) * multiplier + ema;
    result.push(ema);
  }

  return result;
}
