/**
 * lib/graph/index.ts — Barrel export for the probabilistic graph engine.
 *
 * Import everything from `@/lib/graph` and get the full API surface:
 *
 *   import { GraphEngine, fuseSignals, CorrelationTracker, ... } from '@/lib/graph';
 */

// ---------------------------------------------------------------------------
// Core types & factories
// ---------------------------------------------------------------------------
export {
  type SignalCategory,
  type Direction,
  type SignalValue,
  type SignalNode,
  clamp,
  createTechnicalNode,
  createOnChainNode,
  createSentimentNode,
  createDerivativesNode,
  createMacroNode,
  pushHistory,
} from './SignalNode';

// ---------------------------------------------------------------------------
// Bayesian fusion
// ---------------------------------------------------------------------------
export {
  type SignalContribution,
  type FusionResult,
  fuseSignals,
} from './BayesianFusion';

// ---------------------------------------------------------------------------
// Correlation tracker
// ---------------------------------------------------------------------------
export { CorrelationTracker } from './CorrelationTracker';

// ---------------------------------------------------------------------------
// Graph engine (orchestrator)
// ---------------------------------------------------------------------------
export { GraphEngine, type NodeStateSnapshot } from './GraphEngine';

// ---------------------------------------------------------------------------
// Pre-built signal nodes — technical
// ---------------------------------------------------------------------------
export {
  rsiNode,
  macdNode,
  bollingerNode,
  trendNode,
  volumeNode,
  momentumNode,
  allTechnicalNodes,
} from './nodes/technicalNodes';

// ---------------------------------------------------------------------------
// Pre-built signal nodes — on-chain
// ---------------------------------------------------------------------------
export {
  whaleFlowNode,
  mempoolFeeNode,
  liquidationNode,
  allOnChainNodes,
} from './nodes/onchainNodes';

// ---------------------------------------------------------------------------
// Pre-built signal nodes — sentiment
// ---------------------------------------------------------------------------
export {
  fearGreedNode,
  newsNode,
  allSentimentNodes,
} from './nodes/sentimentNodes';

// ---------------------------------------------------------------------------
// Pre-built signal nodes — derivatives
// ---------------------------------------------------------------------------
export {
  fundingRateNode,
  openInterestNode,
  putCallNode,
  allDerivativesNodes,
} from './nodes/derivativesNodes';
