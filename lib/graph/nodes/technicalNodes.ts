/**
 * technicalNodes.ts — Pre-built technical-analysis signal nodes.
 *
 * Each node's `compute` function maps raw indicator values to a normalised
 * SignalValue { value: [-1,+1], confidence: [0,1], timestamp }.
 */

import { clamp, createTechnicalNode, type SignalNode, type SignalValue } from '../SignalNode';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Current time in ms — extracted so tests can mock if needed. */
function now(): number {
  return Date.now();
}

/** Linear interpolation between [a, b] mapped to [outA, outB]. */
function lerp(x: number, a: number, b: number, outA: number, outB: number): number {
  const t = clamp((x - a) / (b - a), 0, 1);
  return outA + t * (outB - outA);
}

// ---------------------------------------------------------------------------
// RSI Node
// ---------------------------------------------------------------------------

/**
 * **RSI (Relative Strength Index)**
 *
 * Inputs: `{ rsi: number }` — RSI value in [0, 100].
 *
 * Mapping:
 *   rsi < 30  → bullish  (+0.8, confidence rises as RSI drops)
 *   rsi > 70  → bearish  (−0.8, confidence rises as RSI rises)
 *   30–70     → linear interpolation between +0.8 and −0.8
 *
 * Confidence is highest at extremes (0 or 100) and lowest at 50.
 */
export const rsiNode: SignalNode = createTechnicalNode(
  'tech:rsi',
  'RSI',
  (inputs: Record<string, number>): SignalValue => {
    const rsi = clamp(inputs.rsi ?? 50, 0, 100);

    // Value: linear map 0→+0.8, 100→-0.8
    const value = clamp(lerp(rsi, 0, 100, 0.8, -0.8), -1, 1);

    // Confidence: higher at extremes, minimum at 50
    const distFromCenter = Math.abs(rsi - 50) / 50; // 0 at 50, 1 at 0/100
    const confidence = clamp(0.3 + distFromCenter * 0.7, 0, 1);

    return { value, confidence, timestamp: now() };
  },
);

// ---------------------------------------------------------------------------
// MACD Node
// ---------------------------------------------------------------------------

/**
 * **MACD (Moving Average Convergence Divergence)**
 *
 * Inputs: `{ macdLine: number, macdSignal: number }`
 *
 * Mapping:
 *   histogram = macdLine − macdSignal
 *   Positive histogram → bullish, negative → bearish.
 *   Value is tanh-compressed to [-1, +1].
 *   Confidence scales with |histogram|.
 */
export const macdNode: SignalNode = createTechnicalNode(
  'tech:macd',
  'MACD',
  (inputs: Record<string, number>): SignalValue => {
    const line = inputs.macdLine ?? 0;
    const signal = inputs.macdSignal ?? 0;
    const histogram = line - signal;

    // tanh compression: keeps output ∈ (-1, +1) without hard clip
    const value = Math.tanh(histogram * 2);

    // Confidence grows with histogram magnitude, capped at 0.95
    const confidence = clamp(Math.min(Math.abs(histogram) * 5, 0.95), 0.1, 0.95);

    return { value, confidence, timestamp: now() };
  },
);

// ---------------------------------------------------------------------------
// Bollinger Band Node
// ---------------------------------------------------------------------------

/**
 * **Bollinger Bands**
 *
 * Inputs: `{ price, upper, lower, width }`
 *
 * Mapping:
 *   Position within band → value.  Close to lower = bullish, close to upper = bearish.
 *   Width (squeeze) → higher confidence when bands are tight.
 */
export const bollingerNode: SignalNode = createTechnicalNode(
  'tech:bollinger',
  'Bollinger Bands',
  (inputs: Record<string, number>): SignalValue => {
    const price = inputs.price ?? 0;
    const upper = inputs.upper ?? 0;
    const lower = inputs.lower ?? 0;
    const width = inputs.width ?? 1;

    const range = upper - lower;
    // Position: 0 at lower band, 1 at upper band
    const position = range > 0 ? clamp((price - lower) / range, 0, 1) : 0.5;

    // Map: position 0 (at lower) → +1 bullish, position 1 (at upper) → -1 bearish
    const value = clamp(1 - 2 * position, -1, 1);

    // Confidence: tighter bands (squeeze) = higher confidence for breakout
    // Width is typically 0–0.2; normalise so a squeeze at ~0.02 → high confidence
    const squeezeConfidence = clamp(1 - width * 10, 0.2, 0.95);
    const confidence = squeezeConfidence;

    return { value, confidence, timestamp: now() };
  },
);

// ---------------------------------------------------------------------------
// Trend Node (SMA Cross)
// ---------------------------------------------------------------------------

/**
 * **Trend (SMA Cross)**
 *
 * Inputs: `{ sma7, sma25, sma99, price }`
 *
 * Mapping:
 *   Golden cross (sma7 > sma25 > sma99) → +1
 *   Death cross  (sma7 < sma25 < sma99) → -1
 *   Confidence based on separation between SMAs.
 */
export const trendNode: SignalNode = createTechnicalNode(
  'tech:trend',
  'Trend (SMA Cross)',
  (inputs: Record<string, number>): SignalValue => {
    const sma7 = inputs.sma7 ?? 0;
    const sma25 = inputs.sma25 ?? 0;
    const sma99 = inputs.sma99 ?? 0;
    const price = inputs.price ?? sma7;

    // Score individual cross conditions
    let score = 0;
    if (sma7 > sma25) score += 0.5; // short-term bullish
    else score -= 0.5;

    if (sma25 > sma99) score += 0.5; // long-term bullish
    else score -= 0.5;

    const value = clamp(score, -1, 1);

    // Confidence: how far apart the SMAs are relative to price
    const separation =
      price > 0
        ? (Math.abs(sma7 - sma25) + Math.abs(sma25 - sma99)) / price
        : 0;
    const confidence = clamp(Math.min(separation * 50, 0.95), 0.15, 0.95);

    return { value, confidence, timestamp: now() };
  },
);

// ---------------------------------------------------------------------------
// Volume Node
// ---------------------------------------------------------------------------

/**
 * **Volume**
 *
 * Inputs: `{ currentVolume, avgVolume }`
 *
 * Mapping:
 *   Volume ratio > 1 with positive momentum → bullish.
 *   Volume ratio < 1 → weak signal.
 *   We use the ratio itself as a confidence multiplier (more volume = more reliable).
 *   Value is slightly bullish when volume spikes (assume confirmation of trend).
 */
export const volumeNode: SignalNode = createTechnicalNode(
  'tech:volume',
  'Volume',
  (inputs: Record<string, number>): SignalValue => {
    const current = inputs.currentVolume ?? 0;
    const avg = inputs.avgVolume ?? 1;

    const ratio = avg > 0 ? current / avg : 1;

    // Above average → mild bullish (trend confirmation). Below → mildly bearish (divergence).
    const value = clamp(Math.tanh((ratio - 1) * 2), -1, 1);

    // Confidence scales with how far the ratio deviates from 1
    const confidence = clamp(Math.abs(ratio - 1) * 0.8, 0.1, 0.9);

    return { value, confidence, timestamp: now() };
  },
);

// ---------------------------------------------------------------------------
// Momentum Node
// ---------------------------------------------------------------------------

/**
 * **Momentum**
 *
 * Inputs: `{ priceChange5m, priceChange1h, priceChange24h }`
 *
 * Weighted composite: 5m (0.5) + 1h (0.3) + 24h (0.2).
 * Values are percentage changes (e.g. 2.5 = +2.5 %).
 * tanh-compressed to [-1, +1].
 */
export const momentumNode: SignalNode = createTechnicalNode(
  'tech:momentum',
  'Momentum',
  (inputs: Record<string, number>): SignalValue => {
    const change5m = inputs.priceChange5m ?? 0;
    const change1h = inputs.priceChange1h ?? 0;
    const change24h = inputs.priceChange24h ?? 0;

    const composite = change5m * 0.5 + change1h * 0.3 + change24h * 0.2;

    const value = Math.tanh(composite / 3); // normalise: ±3 % → tanh ≈ ±0.76

    // Confidence: higher when all timeframes agree in direction
    const signs = [
      Math.sign(change5m),
      Math.sign(change1h),
      Math.sign(change24h),
    ];
    const agreement =
      Math.abs(signs[0] + signs[1] + signs[2]) / 3; // 1 = full agreement, 0.33 = mixed
    const confidence = clamp(0.3 + agreement * 0.6, 0.15, 0.95);

    return { value, confidence, timestamp: now() };
  },
);

// ---------------------------------------------------------------------------
// Convenience array of all technical nodes
// ---------------------------------------------------------------------------

/** All pre-built technical signal nodes. */
export const allTechnicalNodes: SignalNode[] = [
  rsiNode,
  macdNode,
  bollingerNode,
  trendNode,
  volumeNode,
  momentumNode,
];
