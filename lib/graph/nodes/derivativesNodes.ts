/**
 * derivativesNodes.ts — Pre-built derivatives-market signal nodes.
 *
 * These nodes interpret funding rates, open interest dynamics, and
 * put/call ratios to gauge leveraged-market positioning.
 */

import { clamp, createDerivativesNode, type SignalNode, type SignalValue } from '../SignalNode';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function now(): number {
  return Date.now();
}

// ---------------------------------------------------------------------------
// Funding Rate Node
// ---------------------------------------------------------------------------

/**
 * **Funding Rate**
 *
 * Inputs: `{ rate: number }` — perpetual funding rate (e.g. 0.01 = 1 %).
 *
 * Mapping:
 *   High positive rate → overbought → bearish (longs paying premium)
 *   Negative rate       → oversold  → bullish (shorts paying premium)
 *
 * Uses tanh compression so extreme rates don't clip.
 */
export const fundingRateNode: SignalNode = createDerivativesNode(
  'deriv:fundingRate',
  'Funding Rate',
  (inputs: Record<string, number>): SignalValue => {
    const rate = inputs.rate ?? 0;

    // Contrarian: high positive → bearish, negative → bullish
    // Scale factor 100 because typical rates are 0.001–0.05
    const value = clamp(-Math.tanh(rate * 100), -1, 1);

    // Confidence: higher when rate is far from zero
    const absRate = Math.abs(rate);
    const confidence = clamp(Math.min(absRate * 200, 0.95), 0.1, 0.95);

    return { value, confidence, timestamp: now() };
  },
);

// ---------------------------------------------------------------------------
// Open Interest Node
// ---------------------------------------------------------------------------

/**
 * **Open Interest Change**
 *
 * Inputs: `{ oiChange: number, priceChange: number }`
 *   — percentage changes in OI and price over the same period.
 *
 * Mapping:
 *   Rising OI + rising price  → strong bullish trend
 *   Rising OI + falling price → strong bearish trend
 *   Falling OI + rising price → weak bullish (short covering)
 *   Falling OI + falling price → weak bearish (long unwind)
 */
export const openInterestNode: SignalNode = createDerivativesNode(
  'deriv:openInterest',
  'Open Interest',
  (inputs: Record<string, number>): SignalValue => {
    const oiChange = inputs.oiChange ?? 0;
    const priceChange = inputs.priceChange ?? 0;

    const oiRising = oiChange > 0;
    const priceRising = priceChange > 0;

    let value: number;
    let confidence: number;

    if (oiRising && priceRising) {
      // New money entering → strong trend confirmation
      value = clamp(Math.tanh(priceChange * 0.5), 0.2, 1);
      confidence = clamp(0.5 + Math.abs(oiChange) * 0.1, 0.4, 0.95);
    } else if (oiRising && !priceRising) {
      // New shorts entering → bearish pressure
      value = clamp(-Math.tanh(Math.abs(priceChange) * 0.5), -1, -0.2);
      confidence = clamp(0.5 + Math.abs(oiChange) * 0.1, 0.4, 0.95);
    } else if (!oiRising && priceRising) {
      // Short covering → weak bullish
      value = clamp(Math.tanh(priceChange * 0.3), 0.1, 0.6);
      confidence = clamp(0.3 + Math.abs(oiChange) * 0.05, 0.2, 0.7);
    } else {
      // Long unwind → weak bearish
      value = clamp(-Math.tanh(Math.abs(priceChange) * 0.3), -0.6, -0.1);
      confidence = clamp(0.3 + Math.abs(oiChange) * 0.05, 0.2, 0.7);
    }

    return { value, confidence, timestamp: now() };
  },
);

// ---------------------------------------------------------------------------
// Put/Call Ratio Node
// ---------------------------------------------------------------------------

/**
 * **Put/Call Ratio**
 *
 * Inputs: `{ ratio: number }` — e.g. 0.7 means 70 puts per 100 calls.
 *
 * Contrarian mapping:
 *   High ratio (>1.0) → extreme fear → bullish (contrarian)
 *   Low ratio  (<0.5) → extreme greed → bearish (contrarian)
 *   0.5–1.0 → neutral zone
 */
export const putCallNode: SignalNode = createDerivativesNode(
  'deriv:putCall',
  'Put/Call Ratio',
  (inputs: Record<string, number>): SignalValue => {
    const ratio = Math.max(inputs.ratio ?? 0.7, 0);

    // Contrarian: high put/call = fear = bullish
    // Centre at 0.75 (typical neutral), scale outwards
    const deviation = ratio - 0.75;
    const value = clamp(Math.tanh(deviation * 3), -1, 1);

    // Confidence: higher when ratio is far from the neutral zone
    const confidence = clamp(Math.abs(deviation) * 2, 0.1, 0.9);

    return { value, confidence, timestamp: now() };
  },
);

// ---------------------------------------------------------------------------
// Convenience array
// ---------------------------------------------------------------------------

/** All pre-built derivatives signal nodes. */
export const allDerivativesNodes: SignalNode[] = [
  fundingRateNode,
  openInterestNode,
  putCallNode,
];
