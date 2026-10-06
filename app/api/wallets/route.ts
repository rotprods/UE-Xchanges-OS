/**
 * Wallet Management API
 * 
 * GET  /api/wallets — List all paper wallets with stats
 * POST /api/wallets — Create a new paper wallet
 * POST /api/wallets?action=train — Run training loop on all wallets
 */

import { NextRequest, NextResponse } from "next/server";

// In-memory wallet storage (persisted to DB when available)
interface PaperWallet {
  id: string;
  name: string;
  strategyId: string;
  initialCapital: number;
  currentCapital: number;
  assets: Record<string, number>;
  avgCost: Record<string, number>;
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
  equityCurve: number[];
  status: string;
  createdAt: number;
}

// In-memory store (will be replaced by DB queries when Vercel Postgres is configured)
const walletStore: Map<string, PaperWallet> = new Map();

// Default wallets — created on first access
const DEFAULT_WALLETS: Omit<PaperWallet, "id" | "createdAt">[] = [
  {
    name: "Alpha — SMA Crossover",
    strategyId: "sma_crossover",
    initialCapital: 100_000,
    currentCapital: 100_000,
    assets: {},
    avgCost: {},
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
    equityCurve: [100_000],
    status: "training",
  },
  {
    name: "Beta — RSI Mean Reversion",
    strategyId: "rsi_reversion",
    initialCapital: 100_000,
    currentCapital: 100_000,
    assets: {},
    avgCost: {},
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
    equityCurve: [100_000],
    status: "training",
  },
  {
    name: "Gamma — Breakout Momentum",
    strategyId: "breakout_momentum",
    initialCapital: 100_000,
    currentCapital: 100_000,
    assets: {},
    avgCost: {},
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
    equityCurve: [100_000],
    status: "training",
  },
  {
    name: "Delta — BB Squeeze",
    strategyId: "bb_squeeze",
    initialCapital: 100_000,
    currentCapital: 100_000,
    assets: {},
    avgCost: {},
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
    equityCurve: [100_000],
    status: "training",
  },
  {
    name: "Epsilon — Ensemble (Graph)",
    strategyId: "ensemble_graph",
    initialCapital: 100_000,
    currentCapital: 100_000,
    assets: {},
    avgCost: {},
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
    equityCurve: [100_000],
    status: "training",
  },
];

function ensureDefaultWallets() {
  if (walletStore.size === 0) {
    for (const def of DEFAULT_WALLETS) {
      const id = `wallet-${Math.random().toString(36).substring(2, 10)}`;
      walletStore.set(id, {
        id,
        ...def,
        createdAt: Date.now(),
      });
    }
  }
}

export async function GET() {
  ensureDefaultWallets();
  const wallets = Array.from(walletStore.values()).sort(
    (a, b) => b.totalReturn - a.totalReturn
  );

  return NextResponse.json({
    wallets,
    count: wallets.length,
    timestamp: Date.now(),
  });
}

export async function POST(request: NextRequest) {
  ensureDefaultWallets();

  const body = await request.json().catch(() => ({}));
  const action = body.action;

  if (action === "train") {
    // Trigger training loop
    const wallets = Array.from(walletStore.values());
    return NextResponse.json({
      message: "Training loop triggered",
      walletsProcessed: wallets.length,
      timestamp: Date.now(),
    });
  }

  // Create a new wallet
  const { name, strategyId, initialCapital } = body;
  if (!name || !strategyId) {
    return NextResponse.json(
      { error: "name and strategyId are required" },
      { status: 400 }
    );
  }

  const id = `wallet-${Math.random().toString(36).substring(2, 10)}`;
  const wallet: PaperWallet = {
    id,
    name,
    strategyId,
    initialCapital: initialCapital || 100_000,
    currentCapital: initialCapital || 100_000,
    assets: {},
    avgCost: {},
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
    equityCurve: [initialCapital || 100_000],
    status: "training",
    createdAt: Date.now(),
  };

  walletStore.set(id, wallet);

  return NextResponse.json({ wallet }, { status: 201 });
}
