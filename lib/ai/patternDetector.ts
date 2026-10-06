/**
 * Candlestick Pattern Detector
 * Detects classic candlestick reversal/continuation patterns.
 * Pure calculation — no side effects.
 */

export interface PatternResult {
  pattern: string;
  confidence: number; // 0–1
  direction: "BULL" | "BEAR" | "NEUTRAL";
  candleIndex: number;
}

interface Candle {
  open: number;
  high: number;
  low: number;
  close: number;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function bodySize(c: Candle): number {
  return Math.abs(c.close - c.open);
}

function totalRange(c: Candle): number {
  return c.high - c.low;
}

function upperWick(c: Candle): number {
  return c.high - Math.max(c.open, c.close);
}

function lowerWick(c: Candle): number {
  return Math.min(c.open, c.close) - c.low;
}

function isBullish(c: Candle): boolean {
  return c.close > c.open;
}

// ─── Individual Pattern Detectors ────────────────────────────────────────────

/**
 * Doji: body is very small relative to total range (indecision).
 */
function detectDoji(c: Candle, index: number): PatternResult | null {
  const range = totalRange(c);
  if (range === 0) return null;
  const body = bodySize(c);
  const ratio = body / range;
  if (ratio > 0.1) return null; // body must be ≤10% of range

  const confidence = 1 - ratio / 0.1; // closer to 0 body → higher confidence
  return {
    pattern: "Doji",
    confidence: parseFloat(confidence.toFixed(3)),
    direction: "NEUTRAL",
    candleIndex: index,
  };
}

/**
 * Hammer: small body near the top, lower wick > 2× body, tiny upper wick.
 * Bullish reversal after a downtrend.
 */
function detectHammer(c: Candle, index: number): PatternResult | null {
  const body = bodySize(c);
  const lower = lowerWick(c);
  const upper = upperWick(c);
  const range = totalRange(c);

  if (body === 0 || range === 0) return null;
  if (lower < 2 * body) return null; // lower wick must be > 2× body
  if (upper > 0.5 * body) return null; // negligible upper wick

  const confidence = Math.min(1, (lower / body - 2) / 3 + 0.5);
  return {
    pattern: "Hammer",
    confidence: parseFloat(confidence.toFixed(3)),
    direction: "BULL",
    candleIndex: index,
  };
}

/**
 * Shooting Star: small body near the bottom, upper wick > 2× body, tiny lower wick.
 * Bearish reversal after an uptrend.
 */
function detectShootingStar(c: Candle, index: number): PatternResult | null {
  const body = bodySize(c);
  const lower = lowerWick(c);
  const upper = upperWick(c);
  const range = totalRange(c);

  if (body === 0 || range === 0) return null;
  if (upper < 2 * body) return null; // upper wick must be > 2× body
  if (lower > 0.5 * body) return null; // negligible lower wick

  const confidence = Math.min(1, (upper / body - 2) / 3 + 0.5);
  return {
    pattern: "Shooting Star",
    confidence: parseFloat(confidence.toFixed(3)),
    direction: "BEAR",
    candleIndex: index,
  };
}

/**
 * Bullish Engulfing: current bullish candle body fully wraps the previous bearish body.
 */
function detectBullishEngulfing(
  prev: Candle,
  curr: Candle,
  index: number
): PatternResult | null {
  if (isBullish(prev)) return null; // prev must be bearish
  if (!isBullish(curr)) return null; // curr must be bullish
  if (curr.open >= prev.open) return null;
  if (curr.close <= prev.close) return null;

  const prevBody = bodySize(prev);
  const currBody = bodySize(curr);
  const confidence = Math.min(1, 0.6 + (currBody / prevBody - 1) * 0.2);
  return {
    pattern: "Bullish Engulfing",
    confidence: parseFloat(confidence.toFixed(3)),
    direction: "BULL",
    candleIndex: index,
  };
}

/**
 * Bearish Engulfing: current bearish candle body fully wraps the previous bullish body.
 */
function detectBearishEngulfing(
  prev: Candle,
  curr: Candle,
  index: number
): PatternResult | null {
  if (!isBullish(prev)) return null; // prev must be bullish
  if (isBullish(curr)) return null; // curr must be bearish
  if (curr.open <= prev.open) return null;
  if (curr.close >= prev.close) return null;

  const prevBody = bodySize(prev);
  const currBody = bodySize(curr);
  const confidence = Math.min(1, 0.6 + (currBody / prevBody - 1) * 0.2);
  return {
    pattern: "Bearish Engulfing",
    confidence: parseFloat(confidence.toFixed(3)),
    direction: "BEAR",
    candleIndex: index,
  };
}

/**
 * Morning Star: 3-candle bullish reversal.
 * [0] large bearish, [1] small-bodied doji/star, [2] large bullish closing > midpoint of [0].
 */
function detectMorningStar(
  c0: Candle,
  c1: Candle,
  c2: Candle,
  index: number
): PatternResult | null {
  // c0: bearish
  if (isBullish(c0)) return null;
  // c2: bullish
  if (!isBullish(c2)) return null;
  // c1: small body (potential doji/star)
  const c1Body = bodySize(c1);
  const c0Body = bodySize(c0);
  if (c1Body > c0Body * 0.3) return null; // star must be small
  // c2 must close above midpoint of c0
  const c0Mid = c0.open - c0Body / 2;
  if (c2.close < c0Mid) return null;

  const confidence = Math.min(1, 0.65 + (c2.close - c0Mid) / c0Body * 0.35);
  return {
    pattern: "Morning Star",
    confidence: parseFloat(confidence.toFixed(3)),
    direction: "BULL",
    candleIndex: index,
  };
}

// ─── Main Export ─────────────────────────────────────────────────────────────

/**
 * Scan a candle array and return all detected patterns.
 */
export function detectPatterns(candles: Candle[]): PatternResult[] {
  const results: PatternResult[] = [];

  for (let i = 0; i < candles.length; i++) {
    const c = candles[i];

    // Single-candle patterns
    const doji = detectDoji(c, i);
    if (doji) results.push(doji);

    const hammer = detectHammer(c, i);
    if (hammer) results.push(hammer);

    const star = detectShootingStar(c, i);
    if (star) results.push(star);

    // Two-candle patterns
    if (i >= 1) {
      const prev = candles[i - 1];
      const bullEng = detectBullishEngulfing(prev, c, i);
      if (bullEng) results.push(bullEng);

      const bearEng = detectBearishEngulfing(prev, c, i);
      if (bearEng) results.push(bearEng);
    }

    // Three-candle patterns
    if (i >= 2) {
      const c0 = candles[i - 2];
      const c1 = candles[i - 1];
      const morningStar = detectMorningStar(c0, c1, c, i);
      if (morningStar) results.push(morningStar);
    }
  }

  return results;
}
