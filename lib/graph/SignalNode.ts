/**
 * SignalNode.ts — Core types and factory functions for the probabilistic graph engine.
 *
 * Each SignalNode is a vertex in the signal graph. It holds its current value,
 * a confidence level, historical values for correlation analysis, and a compute
 * function that derives the next SignalValue from raw inputs.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** Broad category buckets that group related signal sources. */
export type SignalCategory =
  | 'technical'
  | 'onchain'
  | 'sentiment'
  | 'derivatives'
  | 'macro';

/** Discrete direction labels derived from the continuous score. */
export type Direction =
  | 'STRONG_BUY'
  | 'BUY'
  | 'NEUTRAL'
  | 'SELL'
  | 'STRONG_SELL';

// ---------------------------------------------------------------------------
// Interfaces
// ---------------------------------------------------------------------------

/**
 * A single snapshot of a signal's output.
 *
 * @property value      — normalised to [-1, +1]. -1 = max bearish, +1 = max bullish.
 * @property confidence — [0, 1]. How reliable the signal considers itself right now.
 * @property timestamp  — Unix epoch milliseconds of the reading.
 */
export interface SignalValue {
  value: number;
  confidence: number;
  timestamp: number;
}

/**
 * A node in the probabilistic signal graph.
 *
 * @property id           — unique identifier, e.g. "tech:rsi".
 * @property name         — human-readable label.
 * @property category     — one of the five signal families.
 * @property weight       — [0, 1], tuned by the optimizer over time.
 * @property dependencies — ids of nodes whose output feeds into `compute`.
 * @property current      — latest computed SignalValue.
 * @property history      — circular buffer of the last 100 values for correlation.
 * @property compute      — pure function: raw inputs → SignalValue.
 */
export interface SignalNode {
  id: string;
  name: string;
  category: SignalCategory;
  weight: number;
  dependencies: string[];
  current: SignalValue;
  history: SignalValue[];
  compute: (inputs: Record<string, number>) => SignalValue;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Maximum number of historical values retained per node. */
const MAX_HISTORY = 100;

/**
 * Default weight per category — calibrated so that the sum of default weights
 * across a typical balanced graph ≈ 1.0 when one node per category is present.
 *
 * technical   → 0.25  (price action is the primary signal)
 * derivatives → 0.20  (funding / OI provide strong short-term edge)
 * onchain     → 0.15  (whale flows / mempool are leading indicators)
 * sentiment   → 0.10  (noisy but useful at extremes)
 * macro       → 0.10  (slow-moving backdrop)
 */
const DEFAULT_WEIGHTS: Record<SignalCategory, number> = {
  technical: 0.25,
  derivatives: 0.20,
  onchain: 0.15,
  sentiment: 0.10,
  macro: 0.10,
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Clamp a number into [min, max]. */
export function clamp(x: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, x));
}

/**
 * Build a SignalNode with sensible defaults.
 * The `compute` function is injected by the caller; everything else is
 * derived from category defaults.
 */
function createNode(
  id: string,
  name: string,
  category: SignalCategory,
  computeFn: (inputs: Record<string, number>) => SignalValue,
  dependencies: string[] = [],
): SignalNode {
  const zeroValue: SignalValue = { value: 0, confidence: 0, timestamp: 0 };
  return {
    id,
    name,
    category,
    weight: DEFAULT_WEIGHTS[category],
    dependencies,
    current: { ...zeroValue },
    history: [],
    compute: computeFn,
  };
}

// ---------------------------------------------------------------------------
// Factory functions — one per category
// ---------------------------------------------------------------------------

/**
 * Create a technical-analysis signal node (RSI, MACD, Bollinger, etc.).
 * Default weight: 0.25
 */
export function createTechnicalNode(
  id: string,
  name: string,
  computeFn: (inputs: Record<string, number>) => SignalValue,
  dependencies: string[] = [],
): SignalNode {
  return createNode(id, name, 'technical', computeFn, dependencies);
}

/**
 * Create an on-chain signal node (whale alerts, mempool pressure, etc.).
 * Default weight: 0.15
 */
export function createOnChainNode(
  id: string,
  name: string,
  computeFn: (inputs: Record<string, number>) => SignalValue,
  dependencies: string[] = [],
): SignalNode {
  return createNode(id, name, 'onchain', computeFn, dependencies);
}

/**
 * Create a sentiment signal node (Fear & Greed index, news sentiment, etc.).
 * Default weight: 0.10
 */
export function createSentimentNode(
  id: string,
  name: string,
  computeFn: (inputs: Record<string, number>) => SignalValue,
  dependencies: string[] = [],
): SignalNode {
  return createNode(id, name, 'sentiment', computeFn, dependencies);
}

/**
 * Create a derivatives signal node (funding rate, open interest, put/call).
 * Default weight: 0.20
 */
export function createDerivativesNode(
  id: string,
  name: string,
  computeFn: (inputs: Record<string, number>) => SignalValue,
  dependencies: string[] = [],
): SignalNode {
  return createNode(id, name, 'derivatives', computeFn, dependencies);
}

/**
 * Create a macro signal node (DXY, VIX, bond yields, etc.).
 * Default weight: 0.10
 */
export function createMacroNode(
  id: string,
  name: string,
  computeFn: (inputs: Record<string, number>) => SignalValue,
  dependencies: string[] = [],
): SignalNode {
  return createNode(id, name, 'macro', computeFn, dependencies);
}

// ---------------------------------------------------------------------------
// History management helper (used by GraphEngine)
// ---------------------------------------------------------------------------

/**
 * Push a new SignalValue onto a node's history, keeping the buffer at
 * most `MAX_HISTORY` entries.
 */
export function pushHistory(node: SignalNode, sv: SignalValue): void {
  node.history.push(sv);
  if (node.history.length > MAX_HISTORY) {
    node.history.shift();
  }
}
