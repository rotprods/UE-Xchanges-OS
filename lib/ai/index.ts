/**
 * AI module barrel exports.
 * Import everything from this single entry point.
 *
 * Usage:
 *   import { detectPatterns, analyzeTrend, scanVolatility, calculateSentiment } from "@/lib/ai";
 */

export { detectPatterns } from "./patternDetector";
export type { PatternResult } from "./patternDetector";

export { analyzeTrend } from "./trendAnalyzer";
export type { TrendResult, TrendDirection, SmaCrossSignal } from "./trendAnalyzer";

export { scanVolatility } from "./volatilityScanner";
export type { VolatilityResult, VolatilityState } from "./volatilityScanner";

export { calculateSentiment } from "./sentimentEngine";
export type { SentimentResult, SentimentLabel, SentimentInput } from "./sentimentEngine";

// ─── Intelligence Engine ────────────────────────────────────────────────────
export { DecisionLogger, decisionLogger } from "./DecisionLogger";
export type { AIDecision } from "./DecisionLogger";

export { analyzeNodePerformance, optimizeWeights } from "./WeightOptimizer";
export type { NodePerformance, OptimizationResult } from "./WeightOptimizer";

export { runTrainingEpisode, runFullTrainingCycle, evaluateOpenDecisions } from "./TrainingLoop";
export type { TrainingEpisodeResult, WalletSnapshot } from "./TrainingLoop";
