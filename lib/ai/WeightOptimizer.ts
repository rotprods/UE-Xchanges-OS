/**
 * WeightOptimizer — Adjusts graph node weights based on historical performance.
 * 
 * Runs after each training episode to improve signal accuracy:
 * 1. Looks at all evaluated decisions
 * 2. For each signal node, measures its predictive accuracy
 * 3. Increases weights for nodes that were accurate, decreases for inaccurate
 * 4. Applies learning rate to prevent wild oscillations
 * 5. Normalizes weights so they sum to 1.0
 */

import type { AIDecision } from "./DecisionLogger";

export interface NodePerformance {
  nodeId: string;
  name: string;
  totalContributions: number;
  correctContributions: number;
  accuracy: number;
  avgContribution: number;
  currentWeight: number;
  recommendedWeight: number;
}

export interface OptimizationResult {
  nodesAnalyzed: number;
  adjustments: { nodeId: string; oldWeight: number; newWeight: number; reason: string }[];
  overallAccuracyBefore: number;
  expectedAccuracyAfter: number;
}

/**
 * Analyze how each signal node contributed to correct vs incorrect decisions.
 */
export function analyzeNodePerformance(
  decisions: AIDecision[],
  currentWeights: Record<string, number>
): NodePerformance[] {
  // Aggregate contributions per node
  const nodeStats: Map<string, { correct: number; total: number; contributions: number[] }> =
    new Map();

  for (const decision of decisions) {
    if (decision.wasCorrect === undefined) continue;

    for (const signal of decision.topSignals) {
      if (!nodeStats.has(signal.nodeId)) {
        nodeStats.set(signal.nodeId, { correct: 0, total: 0, contributions: [] });
      }
      const stats = nodeStats.get(signal.nodeId)!;
      stats.total++;
      stats.contributions.push(Math.abs(signal.contribution));
      if (decision.wasCorrect) {
        stats.correct++;
      }
    }
  }

  // Build performance report
  const performances: NodePerformance[] = [];
  for (const [nodeId, stats] of nodeStats) {
    const accuracy = stats.total > 0 ? stats.correct / stats.total : 0.5;
    const avgContribution =
      stats.contributions.length > 0
        ? stats.contributions.reduce((s, c) => s + c, 0) / stats.contributions.length
        : 0;
    const currentWeight = currentWeights[nodeId] ?? 0.1;

    // Recommended weight: scale current weight by accuracy ratio
    // If accuracy > 0.5 → increase; if < 0.5 → decrease
    const accuracyRatio = accuracy / 0.5; // 1.0 at 50% accuracy, 2.0 at 100%
    const recommendedWeight = Math.max(0.01, Math.min(0.5, currentWeight * accuracyRatio));

    performances.push({
      nodeId,
      name: nodeId.replace(/_/g, " ").toUpperCase(),
      totalContributions: stats.total,
      correctContributions: stats.correct,
      accuracy,
      avgContribution,
      currentWeight,
      recommendedWeight,
    });
  }

  return performances.sort((a, b) => b.accuracy - a.accuracy);
}

/**
 * Compute weight adjustments with a learning rate.
 */
export function optimizeWeights(
  currentWeights: Record<string, number>,
  performances: NodePerformance[],
  learningRate: number = 0.1
): OptimizationResult {
  const adjustments: OptimizationResult["adjustments"] = [];
  const newWeights: Record<string, number> = { ...currentWeights };

  // Only adjust nodes with enough data (at least 10 contributions)
  const significantNodes = performances.filter((p) => p.totalContributions >= 10);

  for (const perf of significantNodes) {
    const oldWeight = currentWeights[perf.nodeId] ?? 0.1;
    const targetWeight = perf.recommendedWeight;
    // Apply learning rate: move gradually toward target
    const newWeight = oldWeight + learningRate * (targetWeight - oldWeight);
    const clampedWeight = Math.max(0.01, Math.min(0.5, newWeight));

    if (Math.abs(clampedWeight - oldWeight) > 0.001) {
      newWeights[perf.nodeId] = clampedWeight;

      let reason: string;
      if (perf.accuracy > 0.6) {
        reason = `High accuracy (${(perf.accuracy * 100).toFixed(1)}%) → increasing weight`;
      } else if (perf.accuracy < 0.4) {
        reason = `Low accuracy (${(perf.accuracy * 100).toFixed(1)}%) → decreasing weight`;
      } else {
        reason = `Neutral accuracy (${(perf.accuracy * 100).toFixed(1)}%) → minor adjustment`;
      }

      adjustments.push({
        nodeId: perf.nodeId,
        oldWeight,
        newWeight: clampedWeight,
        reason,
      });
    }
  }

  // Normalize weights to sum to 1.0
  const totalWeight = Object.values(newWeights).reduce((s, w) => s + w, 0);
  if (totalWeight > 0) {
    for (const key of Object.keys(newWeights)) {
      newWeights[key] = newWeights[key] / totalWeight;
    }
  }

  // Calculate accuracy metrics
  const evaluatedDecisionCount = performances.reduce(
    (s, p) => s + p.totalContributions,
    0
  );
  const correctCount = performances.reduce(
    (s, p) => s + p.correctContributions,
    0
  );
  const overallAccuracyBefore =
    evaluatedDecisionCount > 0 ? correctCount / evaluatedDecisionCount : 0.5;

  // Expected accuracy: weighted average of node accuracies with new weights
  let weightedAccuracy = 0;
  let weightSum = 0;
  for (const perf of significantNodes) {
    const w = newWeights[perf.nodeId] ?? 0.1;
    weightedAccuracy += perf.accuracy * w;
    weightSum += w;
  }
  const expectedAccuracyAfter =
    weightSum > 0 ? weightedAccuracy / weightSum : overallAccuracyBefore;

  return {
    nodesAnalyzed: significantNodes.length,
    adjustments,
    overallAccuracyBefore,
    expectedAccuracyAfter,
  };
}
