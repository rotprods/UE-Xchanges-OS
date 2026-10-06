/**
 * sentimentNodes.ts — Pre-built sentiment signal nodes.
 *
 * Sentiment signals are contrarian by nature: extreme fear is bullish,
 * extreme greed is bearish. News sentiment provides a directional bias.
 */

import { clamp, createSentimentNode, type SignalNode, type SignalValue } from '../SignalNode';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function now(): number {
  return Date.now();
}

// ---------------------------------------------------------------------------
// Fear & Greed Node
// ---------------------------------------------------------------------------

/**
 * **Fear & Greed Index**
 *
 * Inputs: `{ value: number }` — index value in [0, 100].
 *
 * Contrarian mapping:
 *   value < 20 (extreme fear)  → bullish  (contrarian buy signal)
 *   value > 80 (extreme greed) → bearish  (contrarian sell signal)
 *   20–80 → linear interpolation
 *
 * Confidence is highest at extremes.
 */
export const fearGreedNode: SignalNode = createSentimentNode(
  'sentiment:fearGreed',
  'Fear & Greed Index',
  (inputs: Record<string, number>): SignalValue => {
    const fg = clamp(inputs.value ?? 50, 0, 100);

    // Contrarian: fear (low values) → bullish, greed (high values) → bearish
    // Linear map: 0 → +1, 100 → -1
    const value = clamp(1 - (fg / 50), -1, 1);

    // Confidence: highest at extremes (<20 or >80), lowest near 50
    const distFromCenter = Math.abs(fg - 50) / 50;
    const confidence = clamp(0.2 + distFromCenter * 0.7, 0.1, 0.9);

    return { value, confidence, timestamp: now() };
  },
);

// ---------------------------------------------------------------------------
// News Sentiment Node
// ---------------------------------------------------------------------------

/**
 * **News Sentiment**
 *
 * Inputs: `{ positiveCount, negativeCount, neutralCount }`
 *   — counts of recent news articles by sentiment category.
 *
 * Mapping:
 *   Net positive ratio → bullish, net negative → bearish.
 *   Confidence scales with total article count (more data = more reliable).
 */
export const newsNode: SignalNode = createSentimentNode(
  'sentiment:news',
  'News Sentiment',
  (inputs: Record<string, number>): SignalValue => {
    const pos = Math.max(inputs.positiveCount ?? 0, 0);
    const neg = Math.max(inputs.negativeCount ?? 0, 0);
    const neu = Math.max(inputs.neutralCount ?? 0, 0);
    const total = pos + neg + neu;

    if (total === 0) {
      return { value: 0, confidence: 0.05, timestamp: now() };
    }

    // Net sentiment ratio: +1 all positive, -1 all negative
    const netRatio = (pos - neg) / total;
    const value = clamp(netRatio, -1, 1);

    // Confidence: more articles → more meaningful
    // ~50 articles is considered "good coverage"
    const coverage = Math.min(total / 50, 1);
    const confidence = clamp(0.15 + coverage * 0.65, 0.1, 0.8);

    return { value, confidence, timestamp: now() };
  },
);

// ---------------------------------------------------------------------------
// Convenience array
// ---------------------------------------------------------------------------

/** All pre-built sentiment signal nodes. */
export const allSentimentNodes: SignalNode[] = [fearGreedNode, newsNode];
