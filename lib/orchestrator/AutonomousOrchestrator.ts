/**
 * AutonomousOrchestrator — The brain of Chronos Quantum.
 * 
 * Runs continuously in the browser via requestAnimationFrame / setInterval.
 * Every evaluation cycle (configurable, default 60s):
 * 
 * 1. Reads latest market data from omniStore
 * 2. Computes all indicators on latest candles
 * 3. Updates all Graph Engine nodes with fresh data
 * 4. Evaluates the Bayesian Fusion → Unified Signal Score
 * 5. For each active paper wallet:
 *    a. Checks if signal score + confidence exceed threshold
 *    b. Decides BUY / SELL / HOLD
 *    c. Executes trade on the paper wallet
 *    d. Logs decision with full reasoning
 * 6. Periodically runs the training loop (every 24h)
 * 7. Persists snapshots + decisions to Supabase
 * 
 * This file is pure logic — no React. It's initialized from AppShell.
 */

import { GraphEngine } from "../graph/GraphEngine";
import {
  allTechnicalNodes,
  allOnChainNodes,
  allSentimentNodes,
  allDerivativesNodes,
} from "../graph/index";
import { CorrelationTracker } from "../graph/CorrelationTracker";
import type { FusionResult } from "../graph/BayesianFusion";
import { PaperWalletManager, type PaperWallet } from "../wallets/PaperWalletManager";
import { decisionLogger } from "../ai/DecisionLogger";
import { runTrainingEpisode, type WalletSnapshot } from "../ai/TrainingLoop";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface OrchestratorConfig {
  evaluationIntervalMs: number;    // How often to evaluate signals (default: 60000 = 1min)
  trainingIntervalMs: number;      // How often to run training (default: 86400000 = 24h)
  minConfidence: number;           // Minimum confidence to execute (default: 0.6)
  minSignalScore: number;          // Min score deviation from 50 to act (default: 15)
  maxPositionPct: number;          // Max % of capital per trade (default: 0.10 = 10%)
  symbols: string[];               // Symbols to trade
  enabled: boolean;                // Master switch
}

export interface OrchestratorState {
  isRunning: boolean;
  lastEvaluation: number;
  lastTraining: number;
  evaluationCount: number;
  currentSignal: FusionResult | null;
  wallets: PaperWallet[];
  logs: OrchestratorLog[];
}

export interface OrchestratorLog {
  timestamp: number;
  type: "evaluation" | "trade" | "training" | "error" | "info";
  message: string;
  data?: any;
}

const DEFAULT_CONFIG: OrchestratorConfig = {
  evaluationIntervalMs: 60_000,
  trainingIntervalMs: 86_400_000,
  minConfidence: 0.6,
  minSignalScore: 15,
  maxPositionPct: 0.10,
  symbols: ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
  enabled: false,
};

// ─── Orchestrator Class ───────────────────────────────────────────────────────

export class AutonomousOrchestrator {
  private graphEngine: GraphEngine;
  private walletManager: PaperWalletManager;
  private config: OrchestratorConfig;
  private state: OrchestratorState;
  private evalTimer: ReturnType<typeof setInterval> | null = null;
  private trainTimer: ReturnType<typeof setInterval> | null = null;
  private onStateChange?: (state: OrchestratorState) => void;

  constructor(config?: Partial<OrchestratorConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };

    // Initialize Graph Engine with all pre-built nodes
    this.graphEngine = new GraphEngine();
    [...allTechnicalNodes, ...allOnChainNodes, ...allSentimentNodes, ...allDerivativesNodes]
      .forEach((node) => this.graphEngine.registerNode(node));

    // Initialize Paper Wallet Manager
    this.walletManager = new PaperWalletManager();

    // Create default wallets
    this.walletManager.createWallet("Alpha — SMA Crossover", "sma_crossover", 100_000);
    this.walletManager.createWallet("Beta — RSI Reversion", "rsi_reversion", 100_000);
    this.walletManager.createWallet("Gamma — Breakout", "breakout_momentum", 100_000);
    this.walletManager.createWallet("Delta — BB Squeeze", "bb_squeeze", 100_000);
    this.walletManager.createWallet("Epsilon — Ensemble", "ensemble_graph", 100_000);

    this.state = {
      isRunning: false,
      lastEvaluation: 0,
      lastTraining: 0,
      evaluationCount: 0,
      currentSignal: null,
      wallets: this.walletManager.getAllWallets(),
      logs: [],
    };
  }

  // ─── Lifecycle ─────────────────────────────────────────────────────────────

  start(): void {
    if (this.state.isRunning) return;
    this.state.isRunning = true;
    this.log("info", "🚀 Autonomous Orchestrator STARTED");

    // Evaluation loop
    this.evalTimer = setInterval(() => {
      this.evaluate();
    }, this.config.evaluationIntervalMs);

    // Training loop
    this.trainTimer = setInterval(() => {
      this.train();
    }, this.config.trainingIntervalMs);

    // Run first evaluation immediately
    setTimeout(() => this.evaluate(), 2000);

    this.emitState();
  }

  stop(): void {
    if (!this.state.isRunning) return;
    if (this.evalTimer) clearInterval(this.evalTimer);
    if (this.trainTimer) clearInterval(this.trainTimer);
    this.evalTimer = null;
    this.trainTimer = null;
    this.state.isRunning = false;
    this.log("info", "⏹ Autonomous Orchestrator STOPPED");
    this.emitState();
  }

  setOnStateChange(cb: (state: OrchestratorState) => void): void {
    this.onStateChange = cb;
  }

  getState(): OrchestratorState {
    return { ...this.state };
  }

  getConfig(): OrchestratorConfig {
    return { ...this.config };
  }

  updateConfig(update: Partial<OrchestratorConfig>): void {
    this.config = { ...this.config, ...update };
    this.log("info", `⚙️ Config updated: ${JSON.stringify(update)}`);
    this.emitState();
  }

  // ─── Core Evaluation ──────────────────────────────────────────────────────

  /**
   * Feed latest market data from the Zustand store into the graph engine.
   */
  feedMarketData(data: {
    tickers: Record<string, { price: string; volume: string; change?: number }>;
    rsi?: number;
    macdLine?: number;
    macdSignal?: number;
    bbUpper?: number;
    bbLower?: number;
    bbWidth?: number;
    sma7?: number;
    sma25?: number;
    sma99?: number;
    fearGreed?: number;
    fundingRate?: number;
    openInterest?: number;
    oiChange?: number;
    putCallRatio?: number;
    whalesBuy?: number;
    whalesSell?: number;
    mempoolFee?: number;
    avgMempoolFee?: number;
    longLiqs?: number;
    shortLiqs?: number;
    positiveNews?: number;
    negativeNews?: number;
    neutralNews?: number;
  }): void {
    const btc = data.tickers["BTCUSDT"];
    const price = btc ? parseFloat(btc.price) : 0;
    const volume = btc ? parseFloat(btc.volume) : 0;
    const change = btc?.change ?? 0;

    // Update technical nodes
    if (data.rsi !== undefined) {
      this.graphEngine.updateNode("rsi", { rsi: data.rsi });
    }
    if (data.macdLine !== undefined && data.macdSignal !== undefined) {
      this.graphEngine.updateNode("macd", { macdLine: data.macdLine, macdSignal: data.macdSignal });
    }
    if (data.bbUpper !== undefined && data.bbLower !== undefined) {
      this.graphEngine.updateNode("bollinger", {
        price,
        upper: data.bbUpper,
        lower: data.bbLower,
        width: data.bbWidth ?? 0,
      });
    }
    if (data.sma7 !== undefined && data.sma25 !== undefined && data.sma99 !== undefined) {
      this.graphEngine.updateNode("trend", {
        sma7: data.sma7,
        sma25: data.sma25,
        sma99: data.sma99,
        price,
      });
    }
    this.graphEngine.updateNode("volume", { currentVolume: volume, avgVolume: volume * 0.8 });
    this.graphEngine.updateNode("momentum", {
      priceChange5m: change * 0.1,
      priceChange1h: change * 0.5,
      priceChange24h: change,
    });

    // On-chain nodes
    if (data.whalesBuy !== undefined || data.whalesSell !== undefined) {
      this.graphEngine.updateNode("whale_flow", {
        buyWhales: data.whalesBuy ?? 0,
        sellWhales: data.whalesSell ?? 0,
      });
    }
    if (data.mempoolFee !== undefined) {
      this.graphEngine.updateNode("mempool_fee", {
        currentFee: data.mempoolFee,
        avgFee: data.avgMempoolFee ?? data.mempoolFee,
      });
    }
    if (data.longLiqs !== undefined || data.shortLiqs !== undefined) {
      this.graphEngine.updateNode("liquidation", {
        longLiqs: data.longLiqs ?? 0,
        shortLiqs: data.shortLiqs ?? 0,
      });
    }

    // Sentiment nodes
    if (data.fearGreed !== undefined) {
      this.graphEngine.updateNode("fear_greed", { value: data.fearGreed });
    }
    if (data.positiveNews !== undefined) {
      this.graphEngine.updateNode("news_sentiment", {
        positiveCount: data.positiveNews ?? 0,
        negativeCount: data.negativeNews ?? 0,
        neutralCount: data.neutralNews ?? 0,
      });
    }

    // Derivatives nodes
    if (data.fundingRate !== undefined) {
      this.graphEngine.updateNode("funding_rate", { rate: data.fundingRate });
    }
    if (data.openInterest !== undefined) {
      this.graphEngine.updateNode("open_interest", {
        oiChange: data.oiChange ?? 0,
        priceChange: change,
      });
    }
    if (data.putCallRatio !== undefined) {
      this.graphEngine.updateNode("put_call", { ratio: data.putCallRatio });
    }
  }

  /**
   * Run a full evaluation cycle.
   */
  private evaluate(): void {
    try {
      // 1. Run graph fusion
      const result = this.graphEngine.evaluate();
      this.state.currentSignal = result;
      this.state.lastEvaluation = Date.now();
      this.state.evaluationCount++;

      // 2. For each wallet, decide and execute
      const wallets = this.walletManager.getAllWallets();
      for (const wallet of wallets) {
        if (wallet.status !== "training" && wallet.status !== "evaluating") continue;

        for (const symbol of this.config.symbols) {
          this.evaluateForWallet(wallet, symbol, result);
        }
      }

      // 3. Update wallet states
      this.state.wallets = this.walletManager.getAllWallets();

      if (this.state.evaluationCount % 10 === 0) {
        this.log("evaluation", `📊 Eval #${this.state.evaluationCount}: Score=${result.score.toFixed(1)}, Dir=${result.direction}, Conf=${(result.confidence * 100).toFixed(0)}%`);
      }

      this.emitState();
    } catch (err: any) {
      this.log("error", `❌ Evaluation failed: ${err.message}`);
    }
  }

  /**
   * Evaluate signal for a specific wallet and symbol.
   */
  private evaluateForWallet(wallet: PaperWallet, symbol: string, signal: FusionResult): void {
    const deviation = Math.abs(signal.score - 50);
    const isBullish = signal.score > 50;

    // Decision logic
    let action: "BUY" | "SELL" | "HOLD" = "HOLD";

    if (deviation >= this.config.minSignalScore && signal.confidence >= this.config.minConfidence) {
      if (isBullish && (!wallet.assets[symbol] || wallet.assets[symbol] <= 0)) {
        action = "BUY";
      } else if (!isBullish && wallet.assets[symbol] && wallet.assets[symbol] > 0) {
        action = "SELL";
      }
    }

    // Log decision
    const decision = decisionLogger.logDecision(
      wallet.id,
      symbol,
      action,
      signal.score,
      signal.confidence,
      signal.reasoning,
      signal.topSignals
    );

    // Execute trade if not HOLD
    if (action !== "HOLD") {
      const tradeAmount = wallet.currentCapital * this.config.maxPositionPct;
      // Estimate price from the signal data (will use store in production)
      const estimatedPrice = this.getEstimatedPrice(symbol);

      if (estimatedPrice > 0) {
        const trade = this.walletManager.executeTrade(
          wallet.id,
          symbol,
          action,
          tradeAmount,
          estimatedPrice,
          {
            score: signal.score,
            confidence: signal.confidence,
            reasoning: signal.reasoning,
          }
        );

        if (trade) {
          decisionLogger.linkTrade(decision.id, trade.id);
          this.log(
            "trade",
            `${action === "BUY" ? "🟢" : "🔴"} ${action} ${symbol} — $${tradeAmount.toFixed(0)} @ ${estimatedPrice.toFixed(2)} | Score: ${signal.score.toFixed(0)} | Wallet: ${wallet.name}`
          );

          // Persist to Supabase (async, non-blocking)
          this.persistTrade(wallet, trade, decision).catch(() => {});
        }
      }
    }
  }

  /**
   * Get estimated price for a symbol from the last known data.
   */
  private lastKnownPrices: Record<string, number> = {};

  setCurrentPrices(prices: Record<string, number>): void {
    this.lastKnownPrices = { ...prices };
  }

  private getEstimatedPrice(symbol: string): number {
    return this.lastKnownPrices[symbol] ?? 0;
  }

  // ─── Training ─────────────────────────────────────────────────────────────

  private train(): void {
    try {
      const wallets = this.walletManager.getAllWallets();
      let episodesRun = 0;

      for (const wallet of wallets) {
        const snapshot: WalletSnapshot = {
          id: wallet.id,
          strategyId: wallet.strategyId,
          totalTrades: wallet.stats.totalTrades,
          winRate: wallet.stats.winRate,
          totalReturn: wallet.stats.totalReturn,
          sharpeRatio: wallet.stats.sharpeRatio,
          maxDrawdown: wallet.stats.maxDrawdown,
          profitFactor: wallet.stats.profitFactor,
          consecutiveLosses: wallet.stats.consecutiveLosses,
          maxConsecutiveLosses: wallet.stats.maxConsecutiveLosses,
          daysActive: wallet.stats.daysActive,
        };

        const weights = this.graphEngine.exportWeights();
        const episode = runTrainingEpisode(snapshot, weights, 0.1);

        // Apply new weights to graph engine
        this.graphEngine.importWeights(episode.newWeights);

        episodesRun++;

        // Persist episode (async)
        this.persistTrainingEpisode(episode).catch(() => {});
      }

      this.state.lastTraining = Date.now();
      this.log(
        "training",
        `🧠 Training complete: ${episodesRun} episodes. Weights adjusted.`
      );

      this.emitState();
    } catch (err: any) {
      this.log("error", `❌ Training failed: ${err.message}`);
    }
  }

  // ─── Persistence ──────────────────────────────────────────────────────────

  private async persistTrade(wallet: PaperWallet, trade: any, decision: any): Promise<void> {
    try {
      const { insertTrade, insertDecision, upsertWallet } = await import("../db/supabase");
      await insertTrade({
        user_id: 1,
        wallet_id: parseInt(wallet.id.replace(/\D/g, "").slice(0, 8)) || 1,
        symbol: trade.symbol,
        side: trade.side,
        quantity: trade.quantity,
        price: trade.price,
        pnl: trade.pnl,
        signal_score: decision.signalScore,
        confidence: decision.confidence,
        reasoning: decision.reasoning,
        timestamp: trade.timestamp,
      });
      await insertDecision({
        timestamp: decision.timestamp,
        wallet_id: parseInt(wallet.id.replace(/\D/g, "").slice(0, 8)) || 1,
        symbol: decision.symbol,
        action: decision.action,
        signal_score: decision.signalScore,
        confidence: decision.confidence,
        reasoning: decision.reasoning,
      });
    } catch {
      // Supabase not configured — silent
    }
  }

  private async persistTrainingEpisode(episode: any): Promise<void> {
    try {
      const { insertTrainingEpisode } = await import("../db/supabase");
      await insertTrainingEpisode({
        wallet_id: parseInt(episode.walletId.replace(/\D/g, "").slice(0, 8)) || 1,
        start_ts: episode.timestamp - 86400000,
        end_ts: episode.timestamp,
        trades_count: episode.tradesCount,
        total_return: episode.totalReturn,
        sharpe_ratio: episode.sharpeRatio,
        win_rate: episode.winRate,
        max_drawdown: episode.maxDrawdown,
        lessons_learned: episode.lessonsLearned,
        weight_adjustments: episode.newWeights,
      });
    } catch {
      // silent
    }
  }

  // ─── Helpers ──────────────────────────────────────────────────────────────

  private log(type: OrchestratorLog["type"], message: string, data?: any): void {
    const entry: OrchestratorLog = { timestamp: Date.now(), type, message, data };
    this.state.logs.unshift(entry);
    if (this.state.logs.length > 200) {
      this.state.logs = this.state.logs.slice(0, 200);
    }
  }

  private emitState(): void {
    this.onStateChange?.({ ...this.state });
  }

  getGraphEngine(): GraphEngine {
    return this.graphEngine;
  }

  getWalletManager(): PaperWalletManager {
    return this.walletManager;
  }
}

// ─── Singleton ──────────────────────────────────────────────────────────────

let _orchestrator: AutonomousOrchestrator | null = null;

export function getOrchestrator(config?: Partial<OrchestratorConfig>): AutonomousOrchestrator {
  if (!_orchestrator) {
    _orchestrator = new AutonomousOrchestrator(config);
  }
  return _orchestrator;
}
