/**
 * On-Balance Volume (OBV) indicator.
 * Cumulative volume metric: adds volume when close rises,
 * subtracts volume when close falls, unchanged when close is flat.
 * Pure calculation — no side effects.
 *
 * @param candles - Array of candle data with close and optional volume.
 *                  If volume is omitted it defaults to 0 for that bar.
 * @returns Array of OBV values, one per input candle.
 */
export function calculateOBV(
  candles: { close: number; volume?: number }[]
): number[] {
  if (candles.length === 0) return [];

  const result: number[] = [];
  let obv = 0;

  // First bar: OBV starts at 0 (no previous close to compare)
  result.push(obv);

  for (let i = 1; i < candles.length; i++) {
    const vol = candles[i].volume ?? 0;

    if (candles[i].close > candles[i - 1].close) {
      obv += vol;
    } else if (candles[i].close < candles[i - 1].close) {
      obv -= vol;
    }
    // If close === prev close, OBV stays the same

    result.push(obv);
  }

  return result;
}
