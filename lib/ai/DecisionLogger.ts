/**
 * DecisionLogger — Records every AI decision with full reasoning chain.
 * 
 * Each decision captures:
 * - What the graph engine saw (signal score, confidence)
 * - What action was taken (BUY/SELL/HOLD)
 * - Why (human-readable reasoning from top signals)
 * - The market snapshot ID at that moment
 * - Later: whether the decision was profitable (filled by evaluator)
 */

export interface AIDecision {
  id: string;
  timestamp: number;
  walletId: string;
  symbol: string;
  action: "BUY" | "SELL" | "HOLD";
  signalScore: number;
  confidence: number;
  reasoning: string;
  topSignals: { nodeId: string; name: string; value: number; contribution: number }[];
  snapshotId?: number;
  tradeId?: string;
  // Filled later by evaluator
  resultPnl?: number;
  wasCorrect?: boolean;
  evaluatedAt?: number;
}

export class DecisionLogger {
  private decisions: AIDecision[] = [];
  private maxInMemory: number;

  constructor(maxInMemory: number = 1000) {
    this.maxInMemory = maxInMemory;
  }

  /**
   * Log a new decision.
   */
  logDecision(
    walletId: string,
    symbol: string,
    action: "BUY" | "SELL" | "HOLD",
    signalScore: number,
    confidence: number,
    reasoning: string,
    topSignals: { nodeId: string; name: string; value: number; contribution: number }[],
    snapshotId?: number
  ): AIDecision {
    const decision: AIDecision = {
      id: `dec-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`,
      timestamp: Date.now(),
      walletId,
      symbol,
      action,
      signalScore,
      confidence,
      reasoning,
      topSignals,
      snapshotId,
    };

    this.decisions.unshift(decision);
    if (this.decisions.length > this.maxInMemory) {
      this.decisions = this.decisions.slice(0, this.maxInMemory);
    }

    return decision;
  }

  /**
   * Link a decision to a trade after execution.
   */
  linkTrade(decisionId: string, tradeId: string): void {
    const decision = this.decisions.find((d) => d.id === decisionId);
    if (decision) {
      decision.tradeId = tradeId;
    }
  }

  /**
   * Evaluate a past decision: was it correct?
   */
  evaluateDecision(decisionId: string, resultPnl: number): void {
    const decision = this.decisions.find((d) => d.id === decisionId);
    if (decision) {
      decision.resultPnl = resultPnl;
      decision.wasCorrect =
        (decision.action === "BUY" && resultPnl > 0) ||
        (decision.action === "SELL" && resultPnl > 0) ||
        (decision.action === "HOLD" && Math.abs(resultPnl) < 0.01);
      decision.evaluatedAt = Date.now();
    }
  }

  /**
   * Get all decisions for a wallet.
   */
  getDecisions(walletId?: string, limit: number = 50): AIDecision[] {
    const filtered = walletId
      ? this.decisions.filter((d) => d.walletId === walletId)
      : this.decisions;
    return filtered.slice(0, limit);
  }

  /**
   * Get accuracy stats for a wallet.
   */
  getAccuracy(walletId: string): {
    total: number;
    evaluated: number;
    correct: number;
    accuracy: number;
    avgConfidence: number;
    avgSignalScore: number;
  } {
    const walletDecisions = this.decisions.filter((d) => d.walletId === walletId);
    const evaluated = walletDecisions.filter((d) => d.wasCorrect !== undefined);
    const correct = evaluated.filter((d) => d.wasCorrect === true);

    return {
      total: walletDecisions.length,
      evaluated: evaluated.length,
      correct: correct.length,
      accuracy: evaluated.length > 0 ? correct.length / evaluated.length : 0,
      avgConfidence:
        walletDecisions.length > 0
          ? walletDecisions.reduce((sum, d) => sum + d.confidence, 0) / walletDecisions.length
          : 0,
      avgSignalScore:
        walletDecisions.length > 0
          ? walletDecisions.reduce((sum, d) => sum + d.signalScore, 0) / walletDecisions.length
          : 0,
    };
  }

  /**
   * Export for DB persistence.
   */
  exportAll(): AIDecision[] {
    return [...this.decisions];
  }

  /**
   * Import from DB.
   */
  importAll(decisions: AIDecision[]): void {
    this.decisions = [...decisions];
  }

  /**
   * Get decisions that still need evaluation.
   */
  getUnevaluated(limit: number = 50): AIDecision[] {
    return this.decisions
      .filter((d) => d.wasCorrect === undefined && d.action !== "HOLD")
      .slice(0, limit);
  }
}

// Singleton instance
export const decisionLogger = new DecisionLogger();
