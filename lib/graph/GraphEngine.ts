/**
 * GraphEngine.ts — Main orchestrator for the probabilistic signal graph.
 *
 * The engine owns the full lifecycle:
 *   1. Register signal nodes
 *   2. Accept raw input updates (single or batch)
 *   3. Maintain correlation history
 *   4. Run Bayesian fusion on demand
 *   5. Expose weight import/export for persistence & optimisation
 */

import { fuseSignals, type FusionResult } from './BayesianFusion';
import { CorrelationTracker } from './CorrelationTracker';
import { pushHistory, type SignalNode, type SignalValue } from './SignalNode';

// ---------------------------------------------------------------------------
// Node state snapshot (returned by getNodeStates)
// ---------------------------------------------------------------------------

/** Lightweight read-only view of a node's current state. */
export interface NodeStateSnapshot {
  id: string;
  name: string;
  category: string;
  value: number;
  confidence: number;
  weight: number;
}

// ---------------------------------------------------------------------------
// GraphEngine
// ---------------------------------------------------------------------------

export class GraphEngine {
  /** All registered signal nodes keyed by id. */
  private nodes: Map<string, SignalNode>;

  /** Rolling Pearson correlation tracker. */
  private correlationTracker: CorrelationTracker;

  /** Most recent fusion result (null before first evaluation). */
  private lastResult: FusionResult | null;

  constructor() {
    this.nodes = new Map();
    this.correlationTracker = new CorrelationTracker();
    this.lastResult = null;
  }

  // -----------------------------------------------------------------------
  // Registration
  // -----------------------------------------------------------------------

  /**
   * Register a signal node in the graph.
   * Throws if a node with the same id already exists.
   */
  registerNode(node: SignalNode): void {
    if (this.nodes.has(node.id)) {
      throw new Error(`GraphEngine: node "${node.id}" is already registered.`);
    }
    this.nodes.set(node.id, node);
  }

  // -----------------------------------------------------------------------
  // Updates
  // -----------------------------------------------------------------------

  /**
   * Feed new raw inputs into a single node, recompute its SignalValue,
   * and record the new value in both the node's history and the
   * correlation tracker.
   *
   * @throws if nodeId is not registered.
   */
  updateNode(nodeId: string, inputs: Record<string, number>): void {
    const node = this.nodes.get(nodeId);
    if (!node) {
      throw new Error(`GraphEngine: unknown node "${nodeId}".`);
    }

    const sv: SignalValue = node.compute(inputs);
    node.current = sv;
    pushHistory(node, sv);
    this.correlationTracker.update(nodeId, sv.value);
  }

  /**
   * Batch-update multiple nodes in a single call.
   * Order of updates follows the order of the array.
   */
  batchUpdate(
    updates: { nodeId: string; inputs: Record<string, number> }[],
  ): void {
    for (const u of updates) {
      this.updateNode(u.nodeId, u.inputs);
    }
  }

  // -----------------------------------------------------------------------
  // Evaluation
  // -----------------------------------------------------------------------

  /**
   * Run Bayesian fusion across all registered nodes and return the result.
   * The correlation matrix is passed in to discount redundant signals.
   */
  evaluate(): FusionResult {
    const allNodes = Array.from(this.nodes.values());
    const matrix = this.correlationTracker.getMatrix();
    const result = fuseSignals(allNodes, matrix);
    this.lastResult = result;
    return result;
  }

  // -----------------------------------------------------------------------
  // Introspection
  // -----------------------------------------------------------------------

  /**
   * Return a snapshot of every node's current state (useful for dashboards).
   */
  getNodeStates(): NodeStateSnapshot[] {
    const states: NodeStateSnapshot[] = [];
    for (const node of this.nodes.values()) {
      states.push({
        id: node.id,
        name: node.name,
        category: node.category,
        value: node.current.value,
        confidence: node.current.confidence,
        weight: node.weight,
      });
    }
    return states;
  }

  /** Return the most recent FusionResult, or null if `evaluate` has not been called. */
  getLastResult(): FusionResult | null {
    return this.lastResult;
  }

  // -----------------------------------------------------------------------
  // Weight management (for optimiser / persistence)
  // -----------------------------------------------------------------------

  /**
   * Override a node's weight. Used by the optimizer after back-testing.
   *
   * @param nodeId    — id of the target node
   * @param newWeight — new weight ∈ [0, 1]
   * @throws if nodeId is unknown or newWeight is out of range.
   */
  adjustWeight(nodeId: string, newWeight: number): void {
    const node = this.nodes.get(nodeId);
    if (!node) {
      throw new Error(`GraphEngine: unknown node "${nodeId}".`);
    }
    if (newWeight < 0 || newWeight > 1) {
      throw new RangeError(
        `GraphEngine: weight must be in [0, 1], got ${newWeight}.`,
      );
    }
    node.weight = newWeight;
  }

  /**
   * Export the current weight map as a plain object (JSON-friendly for DB storage).
   */
  exportWeights(): Record<string, number> {
    const weights: Record<string, number> = {};
    for (const [id, node] of this.nodes) {
      weights[id] = node.weight;
    }
    return weights;
  }

  /**
   * Import a weight map from the database / config.
   * Unknown keys are silently ignored.
   */
  importWeights(weights: Record<string, number>): void {
    for (const [id, w] of Object.entries(weights)) {
      const node = this.nodes.get(id);
      if (node && w >= 0 && w <= 1) {
        node.weight = w;
      }
    }
  }
}
