// Pure backtesting engine — no React, no store imports

export interface BacktestTrade {
  entryPrice: number;
  exitPrice: number;
  pnl: number;
  pnlPct: number;
  entryIndex: number;
  exitIndex: number;
}

export interface BacktestResult {
  trades: BacktestTrade[];
  totalReturn: number;
  winRate: number;
  maxDrawdown: number;
  sharpeRatio: number;
  equityCurve: number[];
  initialCapital: number;
  finalCapital: number;
}

export type Strategy = (
  candles: { close: number }[],
  index: number,
  inPosition: boolean
) => "BUY" | "SELL" | "HOLD";

export function runBacktest(
  candles: { open: number; high: number; low: number; close: number; time: number | string }[],
  strategy: Strategy,
  initialCapital: number = 100000
): BacktestResult {
  const trades: BacktestTrade[] = [];
  const equityCurve: number[] = [];
  let capital = initialCapital;
  let inPosition = false;
  let entryPrice = 0;
  let entryIndex = 0;

  for (let i = 50; i < candles.length; i++) {
    const signal = strategy(candles, i, inPosition);

    if (signal === "BUY" && !inPosition) {
      entryPrice = candles[i].close;
      entryIndex = i;
      inPosition = true;
    } else if (signal === "SELL" && inPosition) {
      const exitPrice = candles[i].close;
      const pnlPct = (exitPrice - entryPrice) / entryPrice;
      const pnl = capital * pnlPct;
      capital += pnl;
      trades.push({ entryPrice, exitPrice, pnl, pnlPct: pnlPct * 100, entryIndex, exitIndex: i });
      inPosition = false;
    }

    equityCurve.push(capital);
  }

  // Close open position at last price
  if (inPosition && candles.length > 0) {
    const exitPrice = candles[candles.length - 1].close;
    const pnlPct = (exitPrice - entryPrice) / entryPrice;
    const pnl = capital * pnlPct;
    capital += pnl;
    trades.push({ entryPrice, exitPrice, pnl, pnlPct: pnlPct * 100, entryIndex, exitIndex: candles.length - 1 });
    equityCurve.push(capital);
  }

  const totalReturn = ((capital - initialCapital) / initialCapital) * 100;
  const winRate = trades.length > 0 ? (trades.filter((t) => t.pnl > 0).length / trades.length) * 100 : 0;

  // Max drawdown
  let peak = initialCapital;
  let maxDrawdown = 0;
  for (const val of equityCurve) {
    if (val > peak) peak = val;
    const dd = ((peak - val) / peak) * 100;
    if (dd > maxDrawdown) maxDrawdown = dd;
  }

  // Sharpe ratio (simplified: daily returns)
  let sharpeRatio = 0;
  if (equityCurve.length > 1) {
    const returns: number[] = [];
    for (let i = 1; i < equityCurve.length; i++) {
      returns.push((equityCurve[i] - equityCurve[i - 1]) / equityCurve[i - 1]);
    }
    const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
    const variance = returns.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / returns.length;
    const std = Math.sqrt(variance);
    sharpeRatio = std > 0 ? (mean / std) * Math.sqrt(252) : 0;
  }

  return {
    trades,
    totalReturn,
    winRate,
    maxDrawdown,
    sharpeRatio,
    equityCurve,
    initialCapital,
    finalCapital: capital,
  };
}
