/**
 * Graduation Checker — evaluates whether a paper wallet strategy
 * meets the minimum performance criteria to advance to the next stage.
 *
 * Pure function — no side effects. Takes wallet stats and optional
 * criteria overrides, returns a detailed result with per-criterion
 * pass/fail and a readiness score from 0-100.
 */

import type { WalletStats } from "./PaperWalletManager";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** Configurable thresholds that a wallet must meet to graduate. */
export interface GraduationCriteria {
  /** Minimum win rate (default 0.55 = 55%). */
  minWinRate: number;
  /** Minimum annualized Sharpe ratio (default 1.5). */
  minSharpe: number;
  /** Maximum drawdown as a fraction (default 0.15 = 15%). */
  maxDrawdown: number;
  /** Minimum total return as a fraction (default 0.10 = 10%). */
  minReturn: number;
  /** Minimum profit factor (default 1.8). */
  minProfitFactor: number;
  /** Maximum consecutive losses allowed (default 5). */
  maxConsecutiveLosses: number;
  /** Minimum number of closed trades (default 100). */
  minTrades: number;
  /** Minimum days the wallet has been active (default 30). */
  minDaysActive: number;
}

/** Pass/fail result for a single criterion. */
export interface CriterionResult {
  criterion: string;
  required: number;
  actual: number;
  passed: boolean;
}

/** Overall graduation evaluation result. */
export interface GraduationResult {
  /** True if every criterion passed. */
  passed: boolean;
  /** Detailed results for each criterion. */
  criteriaResults: CriterionResult[];
  /**
   * Readiness score from 0-100.
   * Base = (criteria_passed / total) × 100, with a bonus for exceeding
   * thresholds by ≥ 20%.
   */
  readinessScore: number;
  /** Human-readable recommendation string. */
  recommendation: string;
}

// ---------------------------------------------------------------------------
// Defaults
// ---------------------------------------------------------------------------

const DEFAULT_CRITERIA: GraduationCriteria = {
  minWinRate: 0.55,
  minSharpe: 1.5,
  maxDrawdown: 0.15,
  minReturn: 0.10,
  minProfitFactor: 1.8,
  maxConsecutiveLosses: 5,
  minTrades: 100,
  minDaysActive: 30,
};

// ---------------------------------------------------------------------------
// Main function
// ---------------------------------------------------------------------------

/**
 * Evaluate whether a wallet's stats satisfy graduation criteria.
 *
 * @param stats    - Current performance statistics of the wallet.
 * @param criteria - Optional partial overrides for the default criteria.
 * @returns Detailed graduation result with readiness score and recommendation.
 */
export function checkGraduation(
  stats: WalletStats,
  criteria?: Partial<GraduationCriteria>
): GraduationResult {
  const c: GraduationCriteria = { ...DEFAULT_CRITERIA, ...criteria };

  // --- Build per-criterion results ---
  const results: CriterionResult[] = [
    {
      criterion: "Win Rate",
      required: c.minWinRate,
      actual: stats.winRate,
      passed: stats.winRate >= c.minWinRate,
    },
    {
      criterion: "Sharpe Ratio",
      required: c.minSharpe,
      actual: stats.sharpeRatio,
      passed: stats.sharpeRatio >= c.minSharpe,
    },
    {
      criterion: "Max Drawdown",
      required: c.maxDrawdown,
      actual: stats.maxDrawdown,
      passed: stats.maxDrawdown <= c.maxDrawdown,
    },
    {
      criterion: "Total Return",
      required: c.minReturn,
      actual: stats.totalReturn,
      passed: stats.totalReturn >= c.minReturn,
    },
    {
      criterion: "Profit Factor",
      required: c.minProfitFactor,
      actual: stats.profitFactor,
      passed:
        stats.profitFactor >= c.minProfitFactor ||
        stats.profitFactor === Infinity,
    },
    {
      criterion: "Max Consecutive Losses",
      required: c.maxConsecutiveLosses,
      actual: stats.maxConsecutiveLosses,
      passed: stats.maxConsecutiveLosses <= c.maxConsecutiveLosses,
    },
    {
      criterion: "Minimum Trades",
      required: c.minTrades,
      actual: stats.totalTrades,
      passed: stats.totalTrades >= c.minTrades,
    },
    {
      criterion: "Days Active",
      required: c.minDaysActive,
      actual: stats.daysActive,
      passed: stats.daysActive >= c.minDaysActive,
    },
  ];

  // --- Calculate readiness score ---
  const passedCount = results.filter((r) => r.passed).length;
  const total = results.length;
  const baseScore = (passedCount / total) * 100;

  // Bonus: for each criterion that exceeds the threshold by ≥ 20%, add up
  // to 1 point per criterion (max bonus = total criteria points).
  let bonusPoints = 0;
  for (const r of results) {
    if (!r.passed) continue;

    // "Lower is better" criteria (drawdown, consecutive losses)
    const isInverted =
      r.criterion === "Max Drawdown" ||
      r.criterion === "Max Consecutive Losses";

    let excessRatio: number;
    if (isInverted) {
      excessRatio =
        r.required === 0 ? 1 : (r.required - r.actual) / r.required;
    } else {
      excessRatio =
        r.required === 0
          ? r.actual > 0
            ? 1
            : 0
          : (r.actual - r.required) / r.required;
    }

    if (excessRatio >= 0.2) {
      bonusPoints += 1;
    }
  }

  // Cap readiness at 100
  const readinessScore = Math.min(100, Math.round(baseScore + bonusPoints));

  // --- Recommendation ---
  const passed = passedCount === total;
  let recommendation: string;

  if (passed && readinessScore >= 90) {
    recommendation =
      "Strategy exceeds all graduation criteria with strong margins. Ready for live sandbox.";
  } else if (passed) {
    recommendation =
      "Strategy meets all graduation criteria. Consider advancing to live sandbox with close monitoring.";
  } else if (passedCount >= total - 2) {
    recommendation = `Strategy is close to graduating (${passedCount}/${total} criteria met). Focus on: ${results
      .filter((r) => !r.passed)
      .map((r) => r.criterion)
      .join(", ")}.`;
  } else {
    recommendation = `Strategy needs significant improvement (${passedCount}/${total} criteria met). Continue training and review failing areas: ${results
      .filter((r) => !r.passed)
      .map((r) => r.criterion)
      .join(", ")}.`;
  }

  return {
    passed,
    criteriaResults: results,
    readinessScore,
    recommendation,
  };
}
