/**
 * Barrel file — re-exports every indicator for convenient imports.
 *
 * Usage:
 *   import { calculateSMA, calculateEMA, calculateRSI, ... } from "@/lib/indicators";
 */

// --- Core trend & average indicators ---
export { calculateSMA } from "./sma";
export { calculateEMA } from "./ema";
export { calculateMACD } from "./macd";
export { calculateBollingerBands } from "./bollingerBands";
export { calculateVWAP } from "./vwap";

// --- Momentum oscillators ---
export { calculateRSI } from "./rsi";
export { calculateStochRSI } from "./stochRsi";
export { calculateCCI } from "./cci";
export { calculateWilliamsR } from "./williamsR";

// --- Trend strength & direction ---
export { calculateADX } from "./adx";
export { calculateSuperTrend } from "./supertrend";

// --- Volatility ---
export { calculateATR } from "./atr";

// --- Volume-based ---
export { calculateOBV } from "./obv";
export { calculateCMF } from "./cmf";
