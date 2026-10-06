/**
 * Sentiment Engine
 * Computes a composite market sentiment score from multiple data sources.
 * Pure calculation — no side effects.
 */

export type SentimentLabel =
  | "EXTREME_FEAR"
  | "FEAR"
  | "NEUTRAL"
  | "GREED"
  | "EXTREME_GREED";

export interface SentimentResult {
  score: number; // 0–100
  label: SentimentLabel;
  color: string; // hex color for UI
  summary: string; // human-readable
}

export interface SentimentInput {
  fearGreedScore: number; // 0–100 from Fear & Greed Index
  rsiValue: number | null; // RSI 0–100, or null if unavailable
  trendDirection: string; // e.g. 'STRONG_BULL', 'BULL', 'NEUTRAL', 'BEAR', 'STRONG_BEAR'
  whaleCount: number; // number of whale alerts in session
  rektCount: number; // number of liquidation events
}

// ─── Weights ──────────────────────────────────────────────────────────────────
const W_FEAR_GREED = 0.30;
const W_RSI = 0.25;
const W_TREND = 0.25;
const W_WHALE = 0.10;
const W_REKT = 0.10;

// ─── Mappers ──────────────────────────────────────────────────────────────────

/** Map RSI → 0–100 sentiment. RSI=30→0, RSI=50→50, RSI=70→100 */
function mapRsi(rsi: number | null): number {
  if (rsi === null) return 50;
  const clamped = Math.max(0, Math.min(100, rsi));
  // Linear: RSI 30 → 0, RSI 70 → 100
  return Math.max(0, Math.min(100, ((clamped - 30) / 40) * 100));
}

/** Map trend direction string → 0–100 sentiment */
function mapTrend(direction: string): number {
  switch (direction) {
    case "STRONG_BULL": return 90;
    case "BULL": return 70;
    case "NEUTRAL": return 50;
    case "BEAR": return 30;
    case "STRONG_BEAR": return 10;
    default: return 50;
  }
}

/**
 * Map whale count → sentiment boost (0–100).
 * High whale buy activity = bullish. We use a log scale capped at 100.
 */
function mapWhaleActivity(whaleCount: number): number {
  if (whaleCount <= 0) return 50;
  // Normalize: assume ~20 whale events = full greed
  return Math.min(100, 50 + (whaleCount / 20) * 50);
}

/**
 * Map rekt count → fear signal (0–100).
 * More liquidations = more fear → lower score.
 */
function mapLiquidationPressure(rektCount: number): number {
  if (rektCount <= 0) return 50;
  // ~20 rekt events = extreme fear territory
  return Math.max(0, 50 - (rektCount / 20) * 50);
}

// ─── Label & Color ────────────────────────────────────────────────────────────

function scoreToLabel(score: number): SentimentLabel {
  if (score >= 80) return "EXTREME_GREED";
  if (score >= 60) return "GREED";
  if (score >= 40) return "NEUTRAL";
  if (score >= 20) return "FEAR";
  return "EXTREME_FEAR";
}

function labelToColor(label: SentimentLabel): string {
  switch (label) {
    case "EXTREME_GREED": return "#00FF66"; // Neon Green
    case "GREED": return "#00F0FF"; // Electric Cyan
    case "NEUTRAL": return "#8B00FF"; // Plasma Purple
    case "FEAR": return "#FF5500"; // Quantum Orange
    case "EXTREME_FEAR": return "#FF0055"; // Blood Red
  }
}

function buildSummary(score: number, label: SentimentLabel, input: SentimentInput): string {
  const rsiStr = input.rsiValue !== null ? ` RSI at ${input.rsiValue.toFixed(0)}` : "";
  const trendStr = input.trendDirection.replace("_", " ");
  const whaleStr =
    input.whaleCount > 5
      ? `Elevated whale activity (${input.whaleCount} alerts) suggesting accumulation.`
      : input.whaleCount > 0
      ? `Moderate whale presence (${input.whaleCount} alerts).`
      : "No significant whale movement detected.";
  const rektStr =
    input.rektCount > 10
      ? `Heavy liquidation cascade (${input.rektCount} events) signals forced selling.`
      : input.rektCount > 0
      ? `Minor liquidations (${input.rektCount} events) noted.`
      : "Liquidation pressure is low.";

  switch (label) {
    case "EXTREME_GREED":
      return `Market in EXTREME GREED (score ${score}).${rsiStr} — overbought conditions. Trend: ${trendStr}. ${whaleStr} ${rektStr} Exercise caution: corrections common at these levels.`;
    case "GREED":
      return `Greed dominates (score ${score}).${rsiStr}. Trend: ${trendStr}. ${whaleStr} ${rektStr} Bulls remain in control but watch for exhaustion.`;
    case "NEUTRAL":
      return `Market sentiment neutral (score ${score}).${rsiStr}. Trend: ${trendStr}. ${whaleStr} ${rektStr} Await directional confirmation before committing.`;
    case "FEAR":
      return `Fear grips the market (score ${score}).${rsiStr}. Trend: ${trendStr}. ${whaleStr} ${rektStr} Potential accumulation zones forming for patient buyers.`;
    case "EXTREME_FEAR":
      return `EXTREME FEAR detected (score ${score}).${rsiStr}. Trend: ${trendStr}. ${whaleStr} ${rektStr} Capitulation risk high — historically a contrarian buy signal.`;
  }
}

// ─── Main Export ─────────────────────────────────────────────────────────────

/**
 * Calculate composite market sentiment.
 */
export function calculateSentiment(input: SentimentInput): SentimentResult {
  const fearGreedComponent = Math.max(0, Math.min(100, input.fearGreedScore));
  const rsiComponent = mapRsi(input.rsiValue);
  const trendComponent = mapTrend(input.trendDirection);
  const whaleComponent = mapWhaleActivity(input.whaleCount);
  const rektComponent = mapLiquidationPressure(input.rektCount);

  const rawScore =
    fearGreedComponent * W_FEAR_GREED +
    rsiComponent * W_RSI +
    trendComponent * W_TREND +
    whaleComponent * W_WHALE +
    rektComponent * W_REKT;

  const score = Math.round(Math.max(0, Math.min(100, rawScore)));
  const label = scoreToLabel(score);
  const color = labelToColor(label);
  const summary = buildSummary(score, label, input);

  return { score, label, color, summary };
}
