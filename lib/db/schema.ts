import {
  pgTable,
  serial,
  varchar,
  integer,
  real,
  jsonb,
  timestamp,
  bigint,
  boolean,
} from "drizzle-orm/pg-core";

// ─── Users ──────────────────────────────────────────────────────────────────────
export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  email: varchar("email", { length: 255 }).unique().notNull(),
  passwordHash: varchar("password_hash", { length: 255 }).notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// ─── Portfolios ─────────────────────────────────────────────────────────────────
export const portfolios = pgTable("portfolios", {
  id: serial("id").primaryKey(),
  userId: integer("user_id")
    .references(() => users.id)
    .notNull(),
  usdt: real("usdt").default(1_000_000).notNull(),
  assets: jsonb("assets").default({}).notNull(),
  avgCost: jsonb("avg_cost").default({}).notNull(),
  updatedAt: timestamp("updated_at").defaultNow().notNull(),
});

// ─── Trades ─────────────────────────────────────────────────────────────────────
export const trades = pgTable("trades", {
  id: serial("id").primaryKey(),
  userId: integer("user_id").notNull(),
  walletId: integer("wallet_id"),
  symbol: varchar("symbol", { length: 32 }).notNull(),
  side: varchar("side", { length: 8 }).notNull(),
  quantity: real("quantity").notNull(),
  price: real("price").notNull(),
  pnl: real("pnl"),
  signalScore: real("signal_score"),
  confidence: real("confidence"),
  reasoning: varchar("reasoning", { length: 1000 }),
  timestamp: bigint("timestamp", { mode: "number" }).notNull(),
});

// ═══════════════════════════════════════════════════════════════════════════════
// INTELLIGENCE ENGINE TABLES
// ═══════════════════════════════════════════════════════════════════════════════

// ─── Market Snapshots (training data for AI) ─────────────────────────────────
export const marketSnapshots = pgTable("market_snapshots", {
  id: serial("id").primaryKey(),
  timestamp: bigint("timestamp", { mode: "number" }).notNull(),
  symbol: varchar("symbol", { length: 32 }).notNull(),
  price: real("price").notNull(),
  open: real("open"),
  high: real("high"),
  low: real("low"),
  volume24h: real("volume_24h"),
  // Technical indicators
  rsi14: real("rsi_14"),
  sma7: real("sma_7"),
  sma25: real("sma_25"),
  sma99: real("sma_99"),
  ema21: real("ema_21"),
  macdLine: real("macd_line"),
  macdSignal: real("macd_signal"),
  macdHistogram: real("macd_histogram"),
  bbUpper: real("bb_upper"),
  bbLower: real("bb_lower"),
  bbWidth: real("bb_width"),
  vwap: real("vwap"),
  adx: real("adx"),
  obv: real("obv"),
  atr14: real("atr_14"),
  // Trend
  trendDirection: varchar("trend_direction", { length: 16 }),
  trendStrength: real("trend_strength"),
  // On-chain
  btcMempoolFee: real("btc_mempool_fee"),
  ethGasGwei: real("eth_gas_gwei"),
  whaleCount1h: integer("whale_count_1h"),
  liquidationVolume1h: real("liquidation_volume_1h"),
  // Derivatives
  fundingRate: real("funding_rate"),
  openInterest: real("open_interest"),
  longShortRatio: real("long_short_ratio"),
  putCallRatio: real("put_call_ratio"),
  // Sentiment
  fearGreedIndex: integer("fear_greed_index"),
  // Macro
  defiTvl: real("defi_tvl"),
  btcDominance: real("btc_dominance"),
  // Graph output
  graphSignalScore: real("graph_signal_score"),
  graphConfidence: real("graph_confidence"),
  graphDirection: varchar("graph_direction", { length: 16 }),
});

// ─── AI Decisions (log of every AI decision) ─────────────────────────────────
export const aiDecisions = pgTable("ai_decisions", {
  id: serial("id").primaryKey(),
  timestamp: bigint("timestamp", { mode: "number" }).notNull(),
  walletId: integer("wallet_id").notNull(),
  symbol: varchar("symbol", { length: 32 }).notNull(),
  action: varchar("action", { length: 16 }).notNull(),
  signalScore: real("signal_score").notNull(),
  confidence: real("confidence").notNull(),
  reasoning: varchar("reasoning", { length: 2000 }).notNull(),
  snapshotId: integer("snapshot_id"),
  tradeId: integer("trade_id"),
  resultPnl: real("result_pnl"),
  wasCorrect: boolean("was_correct"),
  evaluatedAt: bigint("evaluated_at", { mode: "number" }),
});

// ─── Paper Wallets ──────────────────────────────────────────────────────────
export const paperWallets = pgTable("paper_wallets", {
  id: serial("id").primaryKey(),
  name: varchar("name", { length: 100 }).notNull(),
  strategyId: varchar("strategy_id", { length: 100 }).notNull(),
  initialCapital: real("initial_capital").notNull().default(100_000),
  currentCapital: real("current_capital").notNull().default(100_000),
  assets: jsonb("assets").default({}).notNull(),
  avgCost: jsonb("avg_cost").default({}).notNull(),
  totalTrades: integer("total_trades").default(0).notNull(),
  winCount: integer("win_count").default(0).notNull(),
  lossCount: integer("loss_count").default(0).notNull(),
  winRate: real("win_rate").default(0).notNull(),
  sharpeRatio: real("sharpe_ratio").default(0),
  maxDrawdown: real("max_drawdown").default(0),
  totalReturn: real("total_return").default(0),
  profitFactor: real("profit_factor").default(0),
  consecutiveLosses: integer("consecutive_losses").default(0),
  maxConsecutiveLosses: integer("max_consecutive_losses").default(0),
  equityCurve: jsonb("equity_curve").default([]).notNull(),
  status: varchar("status", { length: 16 }).default("training").notNull(),
  graduatedAt: timestamp("graduated_at"),
  liveTier: varchar("live_tier", { length: 16 }),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  lastTradeAt: timestamp("last_trade_at"),
});

// ─── Strategy Definitions ──────────────────────────────────────────────────
export const strategies = pgTable("strategies", {
  id: serial("id").primaryKey(),
  name: varchar("name", { length: 100 }).notNull(),
  description: varchar("description", { length: 500 }),
  type: varchar("type", { length: 32 }).notNull(),
  parameters: jsonb("parameters").default({}).notNull(),
  graphWeights: jsonb("graph_weights").default({}).notNull(),
  symbols: jsonb("symbols").default(["BTCUSDT"]).notNull(),
  isActive: boolean("is_active").default(true),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// ─── Training Episodes ─────────────────────────────────────────────────────
export const trainingEpisodes = pgTable("training_episodes", {
  id: serial("id").primaryKey(),
  walletId: integer("wallet_id").notNull(),
  strategyId: integer("strategy_id"),
  startTimestamp: bigint("start_ts", { mode: "number" }).notNull(),
  endTimestamp: bigint("end_ts", { mode: "number" }),
  tradesCount: integer("trades_count").default(0),
  totalReturn: real("total_return"),
  sharpeRatio: real("sharpe_ratio"),
  winRate: real("win_rate"),
  maxDrawdown: real("max_drawdown"),
  lessonsLearned: jsonb("lessons_learned").default([]),
  weightAdjustments: jsonb("weight_adjustments").default({}),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// ─── Signal History (every graph node value recorded) ────────────────────────
export const signalHistory = pgTable("signal_history", {
  id: serial("id").primaryKey(),
  timestamp: bigint("timestamp", { mode: "number" }).notNull(),
  nodeId: varchar("node_id", { length: 64 }).notNull(),
  value: real("value").notNull(),
  confidence: real("confidence").notNull(),
  symbol: varchar("symbol", { length: 32 }).notNull(),
});
