import { Strategy } from "../engine";
import { calculateSMA } from "../../../lib/indicators";

export const smaCrossoverStrategy: Strategy = (candles, index, inPosition) => {
  if (index < 26) return "HOLD";
  
  const sma7Prev = calculateSMA(candles.slice(0, index), 7);
  const sma25Prev = calculateSMA(candles.slice(0, index), 25);
  const sma7Curr = calculateSMA(candles.slice(0, index + 1), 7);
  const sma25Curr = calculateSMA(candles.slice(0, index + 1), 25);

  const prev7 = sma7Prev[sma7Prev.length - 1];
  const prev25 = sma25Prev[sma25Prev.length - 1];
  const curr7 = sma7Curr[sma7Curr.length - 1];
  const curr25 = sma25Curr[sma25Curr.length - 1];

  if (prev7 === null || prev25 === null || curr7 === null || curr25 === null) return "HOLD";

  // Golden cross: sma7 crosses above sma25
  if (prev7 < prev25 && curr7 >= curr25) return "BUY";
  // Death cross: sma7 crosses below sma25
  if (prev7 > prev25 && curr7 <= curr25) return "SELL";

  return "HOLD";
};
