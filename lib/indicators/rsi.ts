/**
 * Relative Strength Index (RSI) indicator.
 * Standard Wilder smoothing: RS = avgGain / avgLoss.
 * Pure calculation — no side effects.
 */
export function calculateRSI(
  candles: { close: number }[],
  period: number
): (number | null)[] {
  if (period <= 0 || candles.length === 0) return [];

  const result: (number | null)[] = [];

  // We need at least period + 1 candles to compute the first RSI value
  // (period price changes require period + 1 prices)
  if (candles.length < period + 1) {
    return new Array(candles.length).fill(null);
  }

  // First element has no previous candle, so no change — always null
  result.push(null);

  // Compute initial gains and losses over the first `period` changes
  let gainSum = 0;
  let lossSum = 0;

  for (let i = 1; i <= period; i++) {
    const change = candles[i].close - candles[i - 1].close;
    if (change > 0) {
      gainSum += change;
    } else {
      lossSum += Math.abs(change);
    }
    // Indices 1 through period-1 don't have a full window yet
    if (i < period) {
      result.push(null);
    }
  }

  let avgGain = gainSum / period;
  let avgLoss = lossSum / period;

  // First RSI value at index = period
  if (avgLoss === 0) {
    result.push(100);
  } else {
    const rs = avgGain / avgLoss;
    result.push(100 - 100 / (1 + rs));
  }

  // Subsequent values using Wilder smoothing
  for (let i = period + 1; i < candles.length; i++) {
    const change = candles[i].close - candles[i - 1].close;
    const gain = change > 0 ? change : 0;
    const loss = change < 0 ? Math.abs(change) : 0;

    avgGain = (avgGain * (period - 1) + gain) / period;
    avgLoss = (avgLoss * (period - 1) + loss) / period;

    if (avgLoss === 0) {
      result.push(100);
    } else {
      const rs = avgGain / avgLoss;
      result.push(100 - 100 / (1 + rs));
    }
  }

  return result;
}
