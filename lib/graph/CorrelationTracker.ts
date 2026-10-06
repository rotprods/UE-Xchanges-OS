/**
 * CorrelationTracker.ts — Rolling Pearson correlation between signal nodes.
 *
 * Maintains per-node value histories and computes pairwise Pearson
 * correlation coefficients using pure arithmetic (no external libraries).
 *
 * The correlation matrix is consumed by BayesianFusion to discount
 * redundant signals (correlation > 0.8) and avoid double-counting.
 */

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Default maximum number of historical values per node. */
const DEFAULT_MAX_HISTORY = 100;

/** Minimum number of paired observations required for a meaningful correlation. */
const MIN_OBSERVATIONS = 5;

// ---------------------------------------------------------------------------
// Class
// ---------------------------------------------------------------------------

export class CorrelationTracker {
  /** Map from nodeId → rolling value buffer. */
  private histories: Map<string, number[]>;

  /** Maximum buffer length per node. */
  private maxHistory: number;

  /**
   * @param maxHistory — maximum number of values to retain per node.
   *                     Defaults to 100.
   */
  constructor(maxHistory: number = DEFAULT_MAX_HISTORY) {
    this.histories = new Map();
    this.maxHistory = maxHistory;
  }

  // -----------------------------------------------------------------------
  // Public API
  // -----------------------------------------------------------------------

  /**
   * Record a new value for a given node. Values are appended in chronological
   * order; the oldest entry is evicted when the buffer exceeds `maxHistory`.
   */
  update(nodeId: string, value: number): void {
    let buf = this.histories.get(nodeId);
    if (!buf) {
      buf = [];
      this.histories.set(nodeId, buf);
    }
    buf.push(value);
    if (buf.length > this.maxHistory) {
      buf.shift();
    }
  }

  /**
   * Compute the Pearson correlation coefficient between two nodes.
   *
   * Only overlapping (tail-aligned) observations are used. Returns 0 when
   * insufficient data is available or when either series has zero variance.
   *
   * @returns r ∈ [-1, +1]
   */
  getCorrelation(nodeA: string, nodeB: string): number {
    const histA = this.histories.get(nodeA);
    const histB = this.histories.get(nodeB);

    if (!histA || !histB) return 0;

    // Align from the tail (most recent values)
    const n = Math.min(histA.length, histB.length);
    if (n < MIN_OBSERVATIONS) return 0;

    const a = histA.slice(-n);
    const b = histB.slice(-n);

    return pearson(a, b, n);
  }

  /**
   * Build the full pairwise correlation matrix for all tracked nodes.
   *
   * @returns Map<nodeA, Map<nodeB, correlation>>
   */
  getMatrix(): Map<string, Map<string, number>> {
    const ids = Array.from(this.histories.keys());
    const matrix = new Map<string, Map<string, number>>();

    for (const idA of ids) {
      const row = new Map<string, number>();
      for (const idB of ids) {
        row.set(idB, idA === idB ? 1 : this.getCorrelation(idA, idB));
      }
      matrix.set(idA, row);
    }

    return matrix;
  }

  /**
   * Return all pairs of nodes whose absolute correlation exceeds `threshold`.
   * Each pair is returned once (no duplicates or self-pairs).
   *
   * @param threshold — defaults to 0.8
   * @returns Array of [nodeA, nodeB, correlation] tuples, sorted descending.
   */
  getHighlyCorrelated(threshold: number = 0.8): [string, string, number][] {
    const ids = Array.from(this.histories.keys());
    const results: [string, string, number][] = [];

    for (let i = 0; i < ids.length; i++) {
      for (let j = i + 1; j < ids.length; j++) {
        const r = this.getCorrelation(ids[i], ids[j]);
        if (Math.abs(r) > threshold) {
          results.push([ids[i], ids[j], r]);
        }
      }
    }

    // Sort by absolute correlation, descending
    results.sort((a, b) => Math.abs(b[2]) - Math.abs(a[2]));

    return results;
  }
}

// ---------------------------------------------------------------------------
// Pure math — Pearson correlation coefficient
// ---------------------------------------------------------------------------

/**
 * Compute Pearson's r for two equal-length arrays.
 *
 * Formula:
 *   r = (n × Σxy − Σx × Σy) / sqrt((n × Σx² − (Σx)²) × (n × Σy² − (Σy)²))
 *
 * Returns 0 when the denominator is zero (constant series).
 */
function pearson(a: number[], b: number[], n: number): number {
  let sumA = 0;
  let sumB = 0;
  let sumAB = 0;
  let sumA2 = 0;
  let sumB2 = 0;

  for (let i = 0; i < n; i++) {
    const ai = a[i];
    const bi = b[i];
    sumA += ai;
    sumB += bi;
    sumAB += ai * bi;
    sumA2 += ai * ai;
    sumB2 += bi * bi;
  }

  const numerator = n * sumAB - sumA * sumB;
  const denominator = Math.sqrt(
    (n * sumA2 - sumA * sumA) * (n * sumB2 - sumB * sumB),
  );

  if (denominator === 0) return 0;

  return numerator / denominator;
}
