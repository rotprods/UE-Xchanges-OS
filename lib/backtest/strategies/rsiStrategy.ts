import { Strategy } from "../engine";
import { calculateRSI } from "../../../lib/indicators";

export const rsiStrategy: Strategy = (candles, index, inPosition) => {
  if (index < 20) return "HOLD";

  const rsiPrev = calculateRSI(candles.slice(0, index), 14);
  const rsiCurr = calculateRSI(candles.slice(0, index + 1), 14);

  const prev = rsiPrev[rsiPrev.length - 1];
  const curr = rsiCurr[rsiCurr.length - 1];

  if (prev === null || curr === null) return "HOLD";

  // BUY when RSI crosses up through 30 (recovering from oversold)
  if (prev < 30 && curr >= 30 && !inPosition) return "BUY";
  // SELL when RSI crosses up through 70 (overbought)
  if (prev < 70 && curr >= 70 && inPosition) return "SELL";

  return "HOLD";
};
