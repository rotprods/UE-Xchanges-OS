/**
 * Paper Wallet Manager — simulated trading wallet for strategy evaluation.
 *
 * Manages virtual wallets that track positions, trades, equity curves,
 * and performance statistics without risking real capital. Wallets progress
 * through a lifecycle: training → evaluating → graduated → live_sandbox → live_real.
 *
 * Pure in-memory state — call `exportWallet` / `importWallet` for persistence.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** Status lifecycle of a paper wallet. */
export type WalletStatus =
  | "training"
  | "evaluating"
  | "graduated"
  | "live_sandbox"
  | "live_real"
  | "suspended";

/** A single executed paper trade. */
export interface PaperTrade {
  id: string;
  symbol: string;
  side: "BUY" | "SELL";
  quantity: number;
  price: number;
  /** Realized PnL for this trade (null for opening BUYs). */
  pnl: number | null;
  signalScore: number;
  confidence: number;
  reasoning: string;
  timestamp: number;
}

/** Aggregate performance statistics for a wallet. */
export interface WalletStats {
  totalTrades: number;
  winCount: number;
  lossCount: number;
  winRate: number;
  sharpeRatio: number;
  maxDrawdown: number;
  totalReturn: number;
  profitFactor: number;
  consecutiveLosses: number;
  maxConsecutiveLosses: number;
  daysActive: number;
}

/** Full state of a paper wallet. */
export interface PaperWallet {
  id: string;
  name: string;
  strategyId: string;
  initialCapital: number;
  currentCapital: number;
  /** symbol → quantity held */
  assets: Record<string, number>;
  /** symbol → average entry price */
  avgCost: Record<string, number>;
  trades: PaperTrade[];
  equityCurve: number[];
  stats: WalletStats;
  status: WalletStatus;
  createdAt: number;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Generate a pseudo-random UUID-v4-like identifier. */
function generateId(): string {
  const hex = (): string =>
    Math.floor(Math.random() * 0x10000)
      .toString(16)
      .padStart(4, "0");
  return `${hex()}${hex()}-${hex()}-${hex()}-${hex()}-${hex()}${hex()}${hex()}`;
}

/** Create a blank stats object. */
function emptyStats(): WalletStats {
  return {
    totalTrades: 0,
    winCount: 0,
    lossCount: 0,
    winRate: 0,
    sharpeRatio: 0,
    maxDrawdown: 0,
    totalReturn: 0,
    profitFactor: 0,
    consecutiveLosses: 0,
    maxConsecutiveLosses: 0,
    daysActive: 0,
  };
}

// ---------------------------------------------------------------------------
// Manager
// ---------------------------------------------------------------------------

export class PaperWalletManager {
  private wallets: Map<string, PaperWallet> = new Map();

  constructor() {
    this.wallets = new Map();
  }

  // -----------------------------------------------------------------------
  // Wallet CRUD
  // -----------------------------------------------------------------------

  /**
   * Create a new paper wallet.
   *
   * @param name           - Human-readable wallet name.
   * @param strategyId     - ID of the strategy this wallet tracks.
   * @param initialCapital - Starting capital in USD (default 10 000).
   * @returns The newly created PaperWallet.
   */
  createWallet(
    name: string,
    strategyId: string,
    initialCapital: number = 10_000
  ): PaperWallet {
    const wallet: PaperWallet = {
      id: generateId(),
      name,
      strategyId,
      initialCapital,
      currentCapital: initialCapital,
      assets: {},
      avgCost: {},
      trades: [],
      equityCurve: [initialCapital],
      stats: emptyStats(),
      status: "training",
      createdAt: Date.now(),
    };

    this.wallets.set(wallet.id, wallet);
    return wallet;
  }

  /**
   * Execute a simulated trade (BUY or SELL) on a wallet.
   *
   * BUY:  deducts `amountUsd` from capital, adds `amountUsd / price` units.
   * SELL: sells `amountUsd / price` units (capped at holdings), credits
   *       proceeds, and records realized PnL.
   *
   * @returns The PaperTrade record, or `null` if the wallet doesn't exist
   *          or the trade is invalid (e.g. insufficient capital / holdings).
   */
  executeTrade(
    walletId: string,
    symbol: string,
    side: "BUY" | "SELL",
    amountUsd: number,
    price: number,
    signal: { score: number; confidence: number; reasoning: string }
  ): PaperTrade | null {
    const wallet = this.wallets.get(walletId);
    if (!wallet) return null;
    if (amountUsd <= 0 || price <= 0) return null;

    const quantity = amountUsd / price;

    if (side === "BUY") {
      if (amountUsd > wallet.currentCapital) return null;

      // Update average cost
      const currentQty = wallet.assets[symbol] ?? 0;
      const currentCost = wallet.avgCost[symbol] ?? 0;
      const totalCost = currentCost * currentQty + price * quantity;
      const newQty = currentQty + quantity;

      wallet.assets[symbol] = newQty;
      wallet.avgCost[symbol] = newQty === 0 ? 0 : totalCost / newQty;
      wallet.currentCapital -= amountUsd;

      const trade: PaperTrade = {
        id: generateId(),
        symbol,
        side: "BUY",
        quantity,
        price,
        pnl: null,
        signalScore: signal.score,
        confidence: signal.confidence,
        reasoning: signal.reasoning,
        timestamp: Date.now(),
      };

      wallet.trades.push(trade);
      return trade;
    }

    // --- SELL ---
    const held = wallet.assets[symbol] ?? 0;
    if (held <= 0) return null;

    const sellQty = Math.min(quantity, held);
    const sellValue = sellQty * price;
    const costBasis = sellQty * (wallet.avgCost[symbol] ?? 0);
    const pnl = sellValue - costBasis;

    wallet.assets[symbol] = held - sellQty;
    if (wallet.assets[symbol] <= 0) {
      delete wallet.assets[symbol];
      delete wallet.avgCost[symbol];
    }
    wallet.currentCapital += sellValue;

    const trade: PaperTrade = {
      id: generateId(),
      symbol,
      side: "SELL",
      quantity: sellQty,
      price,
      pnl,
      signalScore: signal.score,
      confidence: signal.confidence,
      reasoning: signal.reasoning,
      timestamp: Date.now(),
    };

    wallet.trades.push(trade);
    return trade;
  }

  // -----------------------------------------------------------------------
  // Queries
  // -----------------------------------------------------------------------

  /** Retrieve a wallet by ID, or `null` if not found. */
  getWallet(walletId: string): PaperWallet | null {
    return this.wallets.get(walletId) ?? null;
  }

  /** Retrieve all wallets as an array. */
  getAllWallets(): PaperWallet[] {
    return Array.from(this.wallets.values());
  }

  /**
   * Calculate total equity: cash + mark-to-market value of all positions.
   *
   * @param walletId      - Target wallet.
   * @param currentPrices - Map of symbol → current market price.
   * @returns Total equity in USD, or 0 if the wallet is not found.
   */
  getWalletEquity(
    walletId: string,
    currentPrices: Record<string, number>
  ): number {
    const wallet = this.wallets.get(walletId);
    if (!wallet) return 0;

    let equity = wallet.currentCapital;
    for (const [symbol, qty] of Object.entries(wallet.assets)) {
      const px = currentPrices[symbol] ?? wallet.avgCost[symbol] ?? 0;
      equity += qty * px;
    }
    return equity;
  }

  // -----------------------------------------------------------------------
  // Stats
  // -----------------------------------------------------------------------

  /**
   * Snapshot current equity into the equity curve and recalculate all stats.
   *
   * Call this once per evaluation period (e.g. daily) to keep the
   * equity curve and derived metrics up to date.
   */
  updateStats(
    walletId: string,
    currentPrices: Record<string, number>
  ): void {
    const wallet = this.wallets.get(walletId);
    if (!wallet) return;

    const equity = this.getWalletEquity(walletId, currentPrices);
    wallet.equityCurve.push(equity);

    this.recalculateStats(wallet);
  }

  /**
   * Recalculate every stat field from the wallet's trade history
   * and equity curve.
   */
  private recalculateStats(wallet: PaperWallet): void {
    const sells = wallet.trades.filter(
      (t) => t.side === "SELL" && t.pnl !== null
    );

    const totalTrades = sells.length;
    let winCount = 0;
    let lossCount = 0;
    let grossProfit = 0;
    let grossLoss = 0;
    let consecutiveLosses = 0;
    let maxConsecutiveLosses = 0;

    for (const t of sells) {
      const pnl = t.pnl as number;
      if (pnl >= 0) {
        winCount++;
        grossProfit += pnl;
        consecutiveLosses = 0;
      } else {
        lossCount++;
        grossLoss += Math.abs(pnl);
        consecutiveLosses++;
        if (consecutiveLosses > maxConsecutiveLosses) {
          maxConsecutiveLosses = consecutiveLosses;
        }
      }
    }

    const winRate = totalTrades === 0 ? 0 : winCount / totalTrades;
    const profitFactor = grossLoss === 0 ? grossProfit > 0 ? Infinity : 0 : grossProfit / grossLoss;

    const curve = wallet.equityCurve;
    const totalReturn =
      wallet.initialCapital === 0
        ? 0
        : (curve[curve.length - 1] - wallet.initialCapital) /
          wallet.initialCapital;

    const daysActive = Math.max(
      1,
      Math.floor((Date.now() - wallet.createdAt) / (1000 * 60 * 60 * 24))
    );

    wallet.stats = {
      totalTrades,
      winCount,
      lossCount,
      winRate,
      sharpeRatio: this.calculateSharpe(curve),
      maxDrawdown: this.calculateMaxDrawdown(curve),
      totalReturn,
      profitFactor,
      consecutiveLosses,
      maxConsecutiveLosses,
      daysActive,
    };
  }

  /**
   * Annualized Sharpe ratio from the equity curve.
   * Assumes each data point is one day.
   *
   * Sharpe = (mean(daily returns) / std(daily returns)) × √252
   */
  private calculateSharpe(equityCurve: number[]): number {
    if (equityCurve.length < 2) return 0;

    const returns: number[] = [];
    for (let i = 1; i < equityCurve.length; i++) {
      if (equityCurve[i - 1] === 0) {
        returns.push(0);
      } else {
        returns.push(
          (equityCurve[i] - equityCurve[i - 1]) / equityCurve[i - 1]
        );
      }
    }

    const mean = returns.reduce((a, b) => a + b, 0) / returns.length;

    let varianceSum = 0;
    for (const r of returns) {
      varianceSum += (r - mean) ** 2;
    }
    const std = Math.sqrt(varianceSum / returns.length);

    if (std === 0) return 0;
    return (mean / std) * Math.sqrt(252);
  }

  /**
   * Maximum drawdown (as a positive fraction, e.g. 0.15 = 15%).
   * Peak-to-trough decline over the entire equity curve.
   */
  private calculateMaxDrawdown(equityCurve: number[]): number {
    if (equityCurve.length < 2) return 0;

    let peak = equityCurve[0];
    let maxDD = 0;

    for (const val of equityCurve) {
      if (val > peak) peak = val;
      const dd = peak === 0 ? 0 : (peak - val) / peak;
      if (dd > maxDD) maxDD = dd;
    }

    return maxDD;
  }

  // -----------------------------------------------------------------------
  // Persistence helpers
  // -----------------------------------------------------------------------

  /**
   * Export wallet state as a plain object for DB persistence.
   *
   * @returns Serializable record, or `null` if the wallet is not found.
   */
  exportWallet(walletId: string): Record<string, unknown> | null {
    const wallet = this.wallets.get(walletId);
    if (!wallet) return null;

    return {
      id: wallet.id,
      name: wallet.name,
      strategyId: wallet.strategyId,
      initialCapital: wallet.initialCapital,
      currentCapital: wallet.currentCapital,
      assets: { ...wallet.assets },
      avgCost: { ...wallet.avgCost },
      trades: wallet.trades.map((t) => ({ ...t })),
      equityCurve: [...wallet.equityCurve],
      stats: { ...wallet.stats },
      status: wallet.status,
      createdAt: wallet.createdAt,
    };
  }

  /**
   * Import a previously-exported wallet into the manager.
   * Overwrites any wallet with the same ID.
   */
  importWallet(data: Record<string, unknown>): void {
    const wallet: PaperWallet = {
      id: data.id as string,
      name: data.name as string,
      strategyId: data.strategyId as string,
      initialCapital: data.initialCapital as number,
      currentCapital: data.currentCapital as number,
      assets: (data.assets as Record<string, number>) ?? {},
      avgCost: (data.avgCost as Record<string, number>) ?? {},
      trades: (data.trades as PaperTrade[]) ?? [],
      equityCurve: (data.equityCurve as number[]) ?? [],
      stats: (data.stats as WalletStats) ?? emptyStats(),
      status: (data.status as WalletStatus) ?? "training",
      createdAt: (data.createdAt as number) ?? Date.now(),
    };

    this.wallets.set(wallet.id, wallet);
  }
}
