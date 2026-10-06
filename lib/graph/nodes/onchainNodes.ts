/**
 * onchainNodes.ts — Pre-built on-chain signal nodes.
 *
 * These track whale flows, mempool congestion, and liquidation cascades
 * to provide leading indicators from blockchain data.
 */

import { clamp, createOnChainNode, type SignalNode, type SignalValue } from '../SignalNode';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function now(): number {
  return Date.now();
}

// ---------------------------------------------------------------------------
// Whale Flow Node
// ---------------------------------------------------------------------------

/**
 * **Whale Flow**
 *
 * Inputs: `{ buyWhales: number, sellWhales: number }`
 *   — count or volume of whale-sized transactions on each side.
 *
 * Mapping:
 *   Net buy dominance → bullish, net sell → bearish.
 *   Value is the normalised net ratio.
 *   Confidence scales with total whale activity.
 */
export const whaleFlowNode: SignalNode = createOnChainNode(
  'onchain:whaleFlow',
  'Whale Flow',
  (inputs: Record<string, number>): SignalValue => {
    const buy = Math.max(inputs.buyWhales ?? 0, 0);
    const sell = Math.max(inputs.sellWhales ?? 0, 0);
    const total = buy + sell;

    if (total === 0) {
      return { value: 0, confidence: 0.05, timestamp: now() };
    }

    // Net ratio: +1 = all buys, -1 = all sells
    const netRatio = (buy - sell) / total;
    const value = clamp(netRatio, -1, 1);

    // Confidence grows with total activity (more whales = more meaningful)
    // Assume "significant" threshold at ~20 transactions
    const confidence = clamp(Math.min(total / 20, 1) * 0.85, 0.1, 0.9);

    return { value, confidence, timestamp: now() };
  },
);

// ---------------------------------------------------------------------------
// Mempool Fee Node
// ---------------------------------------------------------------------------

/**
 * **Mempool Fee Pressure**
 *
 * Inputs: `{ currentFee: number, avgFee: number }`
 *
 * Mapping:
 *   High fees relative to average = network congestion = bearish short-term
 *   (congestion often precedes sell-offs or panic).
 *   Low fees = calm network = mildly bullish.
 */
export const mempoolFeeNode: SignalNode = createOnChainNode(
  'onchain:mempoolFee',
  'Mempool Fee Pressure',
  (inputs: Record<string, number>): SignalValue => {
    const current = inputs.currentFee ?? 0;
    const avg = inputs.avgFee ?? 1;

    const ratio = avg > 0 ? current / avg : 1;

    // ratio > 1 → congestion → bearish, ratio < 1 → calm → bullish
    const value = clamp(-Math.tanh((ratio - 1) * 1.5), -1, 1);

    // Confidence scales with how extreme the deviation is
    const confidence = clamp(Math.abs(ratio - 1) * 0.6, 0.1, 0.85);

    return { value, confidence, timestamp: now() };
  },
);

// ---------------------------------------------------------------------------
// Liquidation Node
// ---------------------------------------------------------------------------

/**
 * **Liquidation Cascade**
 *
 * Inputs: `{ longLiqs: number, shortLiqs: number }`
 *   — USD value of liquidations on each side.
 *
 * Mapping:
 *   Large long liquidations → bearish momentum (longs being wiped out).
 *   Large short liquidations → bullish momentum (short squeeze).
 *   Net direction determines value; magnitude determines confidence.
 */
export const liquidationNode: SignalNode = createOnChainNode(
  'onchain:liquidation',
  'Liquidation Cascade',
  (inputs: Record<string, number>): SignalValue => {
    const longLiqs = Math.max(inputs.longLiqs ?? 0, 0);
    const shortLiqs = Math.max(inputs.shortLiqs ?? 0, 0);
    const total = longLiqs + shortLiqs;

    if (total === 0) {
      return { value: 0, confidence: 0.05, timestamp: now() };
    }

    // Net: positive when short liqs dominate (bullish squeeze),
    //       negative when long liqs dominate (bearish cascade)
    const netRatio = (shortLiqs - longLiqs) / total;
    const value = clamp(netRatio, -1, 1);

    // Confidence: higher when liquidation volume is significant
    // Assume $10M total liqs is "notable"
    const magnitude = Math.min(total / 10_000_000, 1);
    const confidence = clamp(0.15 + magnitude * 0.75, 0.1, 0.9);

    return { value, confidence, timestamp: now() };
  },
);

// ---------------------------------------------------------------------------
// Convenience array
// ---------------------------------------------------------------------------

/** All pre-built on-chain signal nodes. */
export const allOnChainNodes: SignalNode[] = [
  whaleFlowNode,
  mempoolFeeNode,
  liquidationNode,
];
