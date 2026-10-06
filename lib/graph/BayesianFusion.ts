/**
 * BayesianFusion.ts — Weighted Bayesian fusion of heterogeneous signal nodes.
 *
 * The fusion pipeline:
 *   1. Filter nodes with confidence > 0.1
 *   2. Discount highly-correlated (r > 0.8) redundant signals
 *   3. Compute confidence-weighted mean score
 *   4. Map [-1,+1] → [0, 100]
 *   5. Classify into Direction
 *   6. Derive overall confidence from top-5 nodes
 *   7. Build human-readable reasoning string
 */

import type { Direction, SignalNode } from './SignalNode';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** A single signal's contribution to the fused result. */
export interface SignalContribution {
  nodeId: string;
  name: string;
  contribution: number;
  value: number;
}

/** The output of the fusion algorithm. */
export interface FusionResult {
  /** Unified score on a 0–100 scale. */
  score: number;
  /** Discrete direction label. */
  direction: Direction;
  /** Aggregate confidence [0, 1]. */
  confidence: number;
  /** Top contributing signals sorted by |contribution| descending. */
  topSignals: SignalContribution[];
  /** Human-readable explanation of the result. */
  reasoning: string;
}

// ---------------------------------------------------------------------------
// Direction thresholds
// ---------------------------------------------------------------------------

/**
 * Map a 0–100 score to a Direction label.
 *
 * | Range   | Direction    |
 * |---------|------------- |
 * | 0–20    | STRONG_SELL  |
 * | 20–40   | SELL         |
 * | 40–60   | NEUTRAL      |
 * | 60–80   | BUY          |
 * | 80–100  | STRONG_BUY   |
 */
function classifyDirection(score: number): Direction {
  if (score < 20) return 'STRONG_SELL';
  if (score < 40) return 'SELL';
  if (score < 60) return 'NEUTRAL';
  if (score < 80) return 'BUY';
  return 'STRONG_BUY';
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Build a mapping from nodeId to its *effective* weight after correlation
 * discounting.
 *
 * For every pair where |correlation| > 0.8, the node with the lower base
 * weight is penalised by 50 %. If both have equal weight, the one that
 * appears later in the array is discounted.
 */
function computeEffectiveWeights(
  nodes: SignalNode[],
  correlationMatrix?: Map<string, Map<string, number>>,
): Map<string, number> {
  const effective = new Map<string, number>();
  for (const n of nodes) {
    effective.set(n.id, n.weight);
  }

  if (!correlationMatrix) return effective;

  const visited = new Set<string>();

  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const a = nodes[i];
      const b = nodes[j];

      const rowA = correlationMatrix.get(a.id);
      if (!rowA) continue;
      const r = rowA.get(b.id);
      if (r === undefined) continue;
      if (Math.abs(r) <= 0.8) continue;

      // Determine which node to discount (lesser weight, or later index)
      const pairKey = [a.id, b.id].sort().join('|');
      if (visited.has(pairKey)) continue;
      visited.add(pairKey);

      const wA = effective.get(a.id) ?? a.weight;
      const wB = effective.get(b.id) ?? b.weight;

      if (wA <= wB) {
        effective.set(a.id, wA * 0.5);
      } else {
        effective.set(b.id, wB * 0.5);
      }
    }
  }

  return effective;
}

/**
 * Produce a short human-readable direction word for reasoning text.
 */
function directionWord(value: number): string {
  if (value > 0.3) return 'bullish';
  if (value < -0.3) return 'bearish';
  return 'neutral';
}

// ---------------------------------------------------------------------------
// Main fusion function
// ---------------------------------------------------------------------------

/**
 * Fuse an array of SignalNodes into a single unified FusionResult.
 *
 * @param nodes             — all registered signal nodes (filtered internally).
 * @param correlationMatrix — optional pairwise Pearson correlations. When
 *                            provided, highly-correlated nodes are discounted.
 */
export function fuseSignals(
  nodes: SignalNode[],
  correlationMatrix?: Map<string, Map<string, number>>,
): FusionResult {
  // 1. Filter nodes with confidence > 0.1
  const active = nodes.filter((n) => n.current.confidence > 0.1);

  // Edge case: no active nodes → neutral result
  if (active.length === 0) {
    return {
      score: 50,
      direction: 'NEUTRAL',
      confidence: 0,
      topSignals: [],
      reasoning: 'No active signals — defaulting to NEUTRAL.',
    };
  }

  // 2. Compute effective weights (with correlation discounting)
  const weights = computeEffectiveWeights(active, correlationMatrix);

  // 3. Weighted mean: rawScore = Σ(w × v × c) / Σ(w × c)
  let numerator = 0;
  let denominator = 0;

  /** Per-node absolute contribution for ranking. */
  const contributions: SignalContribution[] = [];

  for (const node of active) {
    const w = weights.get(node.id) ?? node.weight;
    const v = node.current.value;
    const c = node.current.confidence;

    const contrib = w * v * c;
    numerator += contrib;
    denominator += w * c;

    contributions.push({
      nodeId: node.id,
      name: node.name,
      contribution: contrib,
      value: v,
    });
  }

  const rawScore = denominator === 0 ? 0 : numerator / denominator;

  // 4. Map [-1, +1] → [0, 100]
  const score = Math.round(((rawScore + 1) / 2) * 100 * 100) / 100; // two decimals

  // 5. Direction
  const direction = classifyDirection(score);

  // 6. Overall confidence = mean of top-5 highest-confidence nodes
  const sortedByConfidence = [...active].sort(
    (a, b) => b.current.confidence - a.current.confidence,
  );
  const top5Confidence = sortedByConfidence.slice(0, 5);
  const confidence =
    top5Confidence.reduce((sum, n) => sum + n.current.confidence, 0) /
    top5Confidence.length;

  // 7. Top signals sorted by |contribution|
  contributions.sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));
  const topSignals = contributions.slice(0, 5);

  // 8. Reasoning string
  const reasoning = buildReasoning(score, direction, topSignals);

  return { score, direction, confidence, topSignals, reasoning };
}

// ---------------------------------------------------------------------------
// Reasoning builder
// ---------------------------------------------------------------------------

function buildReasoning(
  score: number,
  direction: Direction,
  topSignals: SignalContribution[],
): string {
  const parts: string[] = [
    `Unified score: ${score.toFixed(1)}/100 → ${direction}.`,
  ];

  if (topSignals.length > 0) {
    parts.push('Key drivers:');
    for (const s of topSignals) {
      const dir = directionWord(s.value);
      const sign = s.contribution >= 0 ? '+' : '';
      parts.push(
        `  • ${s.name} — ${dir} (value ${s.value.toFixed(2)}, contribution ${sign}${s.contribution.toFixed(4)})`,
      );
    }
  }

  return parts.join('\n');
}
