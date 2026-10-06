import { describe, it, expect } from "vitest";
import { runBacktest, Strategy } from "../engine";

// Helper: generate fake candles with uptrend
function makeCandles(count: number, startPrice: number, trend: number) {
  return Array.from({ length: count }, (_, i) => ({
    time: i,
    open: startPrice + i * trend,
    high: startPrice + i * trend + 5,
    low: startPrice + i * trend - 5,
    close: startPrice + i * trend + 2,
  }));
}

describe("runBacktest", () => {
  it("returns correct structure with trades", () => {
    const candles = makeCandles(200, 100, 0.5);

    // Strategy: buy at index 60, sell at index 100
    const strategy: Strategy = (_c, index, inPosition) => {
      if (index === 60 && !inPosition) return "BUY";
      if (index === 100 && inPosition) return "SELL";
      return "HOLD";
    };

    const result = runBacktest(candles, strategy);

    expect(result.trades.length).toBe(1);
    expect(result.initialCapital).toBe(100000);
    expect(result.finalCapital).toBeGreaterThan(result.initialCapital);
    expect(result.totalReturn).toBeGreaterThan(0);
    expect(result.winRate).toBe(100);
    expect(result.equityCurve.length).toBeGreaterThan(0);
    expect(result.maxDrawdown).toBeGreaterThanOrEqual(0);
  });

  it("handles strategy that never trades", () => {
    const candles = makeCandles(200, 100, 1);
    const strategy: Strategy = () => "HOLD";

    const result = runBacktest(candles, strategy);

    expect(result.trades).toHaveLength(0);
    expect(result.finalCapital).toBe(100000);
    expect(result.totalReturn).toBe(0);
    expect(result.winRate).toBe(0);
  });

  it("closes open positions at end", () => {
    const candles = makeCandles(200, 100, 1);

    // Buy and never sell
    const strategy: Strategy = (_c, index, inPosition) => {
      if (index === 60 && !inPosition) return "BUY";
      return "HOLD";
    };

    const result = runBacktest(candles, strategy);

    // Should have auto-closed the position
    expect(result.trades.length).toBe(1);
    expect(result.trades[0].exitIndex).toBe(candles.length - 1);
  });

  it("calculates drawdown correctly for losing trades", () => {
    // Downtrend candles
    const candles = makeCandles(200, 1000, -2);

    const strategy: Strategy = (_c, index, inPosition) => {
      if (index === 60 && !inPosition) return "BUY";
      if (index === 150 && inPosition) return "SELL";
      return "HOLD";
    };

    const result = runBacktest(candles, strategy);

    expect(result.totalReturn).toBeLessThan(0);
    expect(result.maxDrawdown).toBeGreaterThan(0);
  });

  it("accepts custom initial capital", () => {
    const candles = makeCandles(200, 100, 1);
    const strategy: Strategy = () => "HOLD";

    const result = runBacktest(candles, strategy, 500000);

    expect(result.initialCapital).toBe(500000);
    expect(result.finalCapital).toBe(500000);
  });
});
