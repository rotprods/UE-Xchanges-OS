/**
 * Stochastic RSI indicator.
 * Applies the Stochastic oscillator formula to RSI values instead of price,
 * producing a more sensitive momentum oscillator bounded between 0 and 100.
 * Pure calculation — no side effects.
 *
 * @param candles     - Array of candle data with close prices.
 * @param rsiPeriod   - Period for the underlying RSI calculation (default 14).
 * @param stochPeriod - Look-back period for the Stochastic formula (default 14).
 * @returns Object with `k` (raw %K) and `d` (3-period SMA of %K) arrays,
 *          aligned to input indices with leading nulls for warm-up.
 */
export function calculateStochRSI(
  candles: { close: number }[],
  rsiPeriod: number = 14,
  stochPeriod: number = 14
): { k: (number | null)[]; d: (number | null)[] } {
  const len = candles.length;

  if (rsiPeriod <= 0 || stochPeriod <= 0 || len === 0) {
    return { k: [], d: [] };
  }

  // --- Step 1: Calculate RSI using Wilder smoothing ---
  const rsiValues: (number | null)[] = [];

  if (len < rsiPeriod + 1) {
    return {
      k: new Array(len).fill(null),
      d: new Array(len).fill(null),
    };
  }

  // First element — no change
  rsiValues.push(null);

  let gainSum = 0;
  let lossSum = 0;

  for (let i = 1; i <= rsiPeriod; i++) {
    const change = candles[i].close - candles[i - 1].close;
    if (change > 0) gainSum += change;
    else lossSum += Math.abs(change);
    if (i < rsiPeriod) rsiValues.push(null);
  }

  let avgGain = gainSum / rsiPeriod;
  let avgLoss = lossSum / rsiPeriod;

  if (avgLoss === 0) {
    rsiValues.push(100);
  } else {
    const rs = avgGain / avgLoss;
    rsiValues.push(100 - 100 / (1 + rs));
  }

  for (let i = rsiPeriod + 1; i < len; i++) {
    const change = candles[i].close - candles[i - 1].close;
    const gain = change > 0 ? change : 0;
    const loss = change < 0 ? Math.abs(change) : 0;

    avgGain = (avgGain * (rsiPeriod - 1) + gain) / rsiPeriod;
    avgLoss = (avgLoss * (rsiPeriod - 1) + loss) / rsiPeriod;

    if (avgLoss === 0) {
      rsiValues.push(100);
    } else {
      const rs = avgGain / avgLoss;
      rsiValues.push(100 - 100 / (1 + rs));
    }
  }

  // --- Step 2: Apply Stochastic formula to non-null RSI values ---
  const k: (number | null)[] = new Array(len).fill(null);
  const d: (number | null)[] = new Array(len).fill(null);

  // We need stochPeriod consecutive non-null RSI values.
  // First non-null RSI is at index = rsiPeriod.
  // First valid K is at index = rsiPeriod + stochPeriod - 1.
  const firstK = rsiPeriod + stochPeriod - 1;

  if (firstK >= len) {
    return { k, d };
  }

  for (let i = firstK; i < len; i++) {
    let minRSI = Infinity;
    let maxRSI = -Infinity;

    for (let j = i - stochPeriod + 1; j <= i; j++) {
      const rsi = rsiValues[j] as number;
      if (rsi < minRSI) minRSI = rsi;
      if (rsi > maxRSI) maxRSI = rsi;
    }

    const range = maxRSI - minRSI;
    k[i] = range === 0 ? 100 : ((rsiValues[i] as number) - minRSI) / range * 100;
  }

  // --- Step 3: D = 3-period SMA of K ---
  const dPeriod = 3;
  const firstD = firstK + dPeriod - 1;

  for (let i = firstD; i < len; i++) {
    let sum = 0;
    for (let j = i - dPeriod + 1; j <= i; j++) {
      sum += k[j] as number;
    }
    d[i] = sum / dPeriod;
  }

  return { k, d };
}
