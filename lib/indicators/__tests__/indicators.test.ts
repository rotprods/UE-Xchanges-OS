import { describe, it, expect } from "vitest";
import { calculateSMA } from "../sma";
import { calculateRSI } from "../rsi";

describe("calculateSMA", () => {
  it("returns correct SMA for known data", () => {
    const candles = [
      { close: 10 },
      { close: 20 },
      { close: 30 },
      { close: 40 },
      { close: 50 },
    ];
    const result = calculateSMA(candles, 3);
    expect(result).toHaveLength(5);
    expect(result[0]).toBeNull();
    expect(result[1]).toBeNull();
    expect(result[2]).toBeCloseTo(20); // (10+20+30)/3
    expect(result[3]).toBeCloseTo(30); // (20+30+40)/3
    expect(result[4]).toBeCloseTo(40); // (30+40+50)/3
  });

  it("returns empty array for empty candles", () => {
    expect(calculateSMA([], 5)).toEqual([]);
  });

  it("returns empty array for invalid period", () => {
    expect(calculateSMA([{ close: 10 }], 0)).toEqual([]);
  });

  it("handles period of 1 (identity)", () => {
    const candles = [{ close: 5 }, { close: 15 }, { close: 25 }];
    const result = calculateSMA(candles, 1);
    expect(result).toEqual([5, 15, 25]);
  });
});

describe("calculateRSI", () => {
  it("returns values between 0 and 100", () => {
    const candles = Array.from({ length: 30 }, (_, i) => ({
      close: 100 + Math.sin(i) * 10,
    }));
    const result = calculateRSI(candles, 14);
    const nonNullValues = result.filter((v) => v !== null) as number[];
    expect(nonNullValues.length).toBeGreaterThan(0);
    nonNullValues.forEach((val) => {
      expect(val).toBeGreaterThanOrEqual(0);
      expect(val).toBeLessThanOrEqual(100);
    });
  });

  it("returns 100 for only-gains data", () => {
    const candles = Array.from({ length: 20 }, (_, i) => ({
      close: 100 + i * 5,
    }));
    const result = calculateRSI(candles, 14);
    const lastVal = result[result.length - 1];
    expect(lastVal).toBe(100);
  });

  it("returns empty for empty input", () => {
    expect(calculateRSI([], 14)).toEqual([]);
  });

  it("returns all nulls for insufficient data", () => {
    const candles = [{ close: 10 }, { close: 20 }];
    const result = calculateRSI(candles, 14);
    expect(result.every((v) => v === null)).toBe(true);
  });
});
