import { create } from 'zustand';

// ─── Shared types ────────────────────────────────────────────────────────────

export interface NewsItem {
  id: string;
  title: string;
  body: string;
  url: string;
  source: string;
  publishedAt: number;
  categories: string;
  imageUrl: string;
}

export interface DefiChainEntry {
  name: string;
  tvl: number;
  change24h: number;
}

export interface DefiTVLState {
  total: number;
  change24h: number;
  chains: DefiChainEntry[];
}

export interface Trade {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  timestamp: number;
  pnl?: number;
}

export interface TickerData {
  symbol: string;
  price: string;
  open: string;
  high: string;
  low: string;
  volume: string;
  volumeQuote: string;
  change?: number;
}

export interface MempoolEvent {
  hash: string;
  network: string;
  gas: number;
  value: string;
  time: number;
}

export interface SystemStats {
  totalVolume24h: number;
  txsPerSecond: number;
  gasGwei: number;
  lastUpdate: number;
}

export interface OrderBookLevel {
  price: number;
  size: number;
}

export interface OrderBookData {
  bids: OrderBookLevel[];
  asks: OrderBookLevel[];
}

export interface WhaleAlert {
  id: string;
  token: string;
  amountUsd: string;
  from: string;
  to: string;
  time: number;
}

export interface CandleData {
  time: number | string;
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface AIExecutionLog {
  id: string;
  time: string;
  action: string;
  reason: string;
  color: string;
}

interface OmniStore {
  tickers: Record<string, TickerData>;
  mempoolEvents: MempoolEvent[];
  orderBook: OrderBookData;
  whaleAlerts: WhaleAlert[];
  latestCandle: CandleData | null;
  stats: SystemStats;
  pulseTrigger: number;
  audioEnabled: boolean;
  setTickers: (tickers: Record<string, TickerData>) => void;
  setStats: (stats: SystemStats) => void;
  incrementPulse: () => void;
  addMempoolEvent: (event: MempoolEvent) => void;
  setOrderBook: (orderBook: OrderBookData) => void;
  addWhaleAlert: (alert: WhaleAlert) => void;
  setLatestCandle: (candle: CandleData) => void;
  
  marketMode: "CRYPTO" | "STOCKS";
  setMarketMode: (mode: "CRYPTO" | "STOCKS") => void;
  
  chartSymbol: string;
  chartInterval: string;
  setChartSymbol: (symbol: string) => void;
  setChartInterval: (interval: string) => void;
  
  toasts: { id: string; title: string; message: string; type: "whale" | "system" | "network" | "rekt" }[];
  addToast: (title: string, message: string, type: "whale" | "system" | "network" | "rekt") => void;
  removeToast: (id: string) => void;
  
  panicLevel: number;
  triggerPanic: () => void;
  decayPanic: () => void;
  
  portfolio: { usdt: number; assets: Record<string, number>; avgCost: Record<string, number> };
  tradeHistory: Trade[];
  addTrade: (trade: Trade) => void;
  executeTrade: (symbol: string, side: "BUY" | "SELL", amountUsd: number, price: number) => void;
  
  toggleAudio: () => void;

  // ─── DeFi & News ────────────────────────────────────────────────────────
  defiTVL: DefiTVLState;
  setDefiTVL: (data: DefiTVLState) => void;

  newsItems: NewsItem[];
  setNewsItems: (items: NewsItem[]) => void;

  // ─── AI Trader ────────────────────────────────────────────────────────
  autoTradeEnabled: boolean;
  toggleAutoTrade: () => void;
  aiExecutionLogs: AIExecutionLog[];
  addAILog: (log: Omit<AIExecutionLog, 'id'>) => void;

  // ─── Real Exchange Execution ────────────────────────────────────────────
  realModeEnabled: boolean;
  toggleRealMode: () => void;
  apiKeys: { binanceApiKey: string; binanceSecret: string };
  setApiKeys: (keys: { binanceApiKey: string; binanceSecret: string }) => void;

  // ─── RPG Gamification ───────────────────────────────────────────────────
  playerLevel: number;
  playerExp: number;
  currentTheme: string;
  addExp: (amount: number) => void;
  setTheme: (theme: string) => void;
}

export const useOmniStore = create<OmniStore>((set, get) => ({
  tickers: {},
  mempoolEvents: [],
  orderBook: { bids: [], asks: [] },
  whaleAlerts: [],
  latestCandle: null,
  
  marketMode: "CRYPTO",
  
  chartSymbol: "BTCUSDT",
  chartInterval: "1m",
  
  toasts: [],
  
  stats: {
    totalVolume24h: 0,
    txsPerSecond: 0,
    gasGwei: 45,
    lastUpdate: Date.now(),
  },
  pulseTrigger: 0,
  audioEnabled: false,

  defiTVL: { total: 0, change24h: 0, chains: [] },
  newsItems: [],
  
  autoTradeEnabled: false,
  aiExecutionLogs: [],

  realModeEnabled: false,
  apiKeys: { binanceApiKey: '', binanceSecret: '' },

  playerLevel: 1,
  playerExp: 0,
  currentTheme: 'cyberpunk',
  
  setTickers: (tickers) => set({ tickers }),
  setStats: (stats) => set({ stats }),
  incrementPulse: () => set((state) => ({ pulseTrigger: state.pulseTrigger + 1 })),
  addMempoolEvent: (event) => set((state) => {
    const newEvents = [event, ...state.mempoolEvents].slice(0, 50);
    return { mempoolEvents: newEvents };
  }),
  setOrderBook: (orderBook) => set({ orderBook }),
  addWhaleAlert: (alert) => set((state) => {
    const newAlerts = [alert, ...state.whaleAlerts].slice(0, 10); // Keep last 10
    return { whaleAlerts: newAlerts };
  }),
  setLatestCandle: (candle) => set({ latestCandle: candle }),
  
  setMarketMode: (mode) => set({ marketMode: mode }),
  
  setChartSymbol: (symbol) => set({ chartSymbol: symbol }),
  setChartInterval: (interval) => set({ chartInterval: interval }),
  
  addToast: (title, message, type) => set((state) => ({
    toasts: [...state.toasts, { id: Math.random().toString(36).substring(7), title, message, type }]
  })),
  removeToast: (id) => set((state) => ({
    toasts: state.toasts.filter(t => t.id !== id)
  })),
  
  panicLevel: 0,
  triggerPanic: () => set({ panicLevel: 1.0 }),
  decayPanic: () => set((state) => ({ panicLevel: Math.max(0, state.panicLevel - 0.05) })),
  
  portfolio: { usdt: 1000000, assets: {}, avgCost: {} },
  tradeHistory: [],
  addTrade: (trade) => set((state) => ({
    tradeHistory: [trade, ...state.tradeHistory].slice(0, 200),
  })),
  executeTrade: async (symbol, side, amountUsd, price) => {
    const state = get();
    const qty = amountUsd / price;

    if (state.realModeEnabled) {
      try {
        const res = await fetch('/api/trade', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ symbol, side, amount: qty })
        });
        const data = await res.json();
        if (!res.ok || !data.success) {
          console.error('Real trade failed:', data.error);
          get().addToast('Trade Failed', data.error || 'Failed to execute real trade', 'rekt');
          return;
        }
        get().addToast('Trade Executed', `Real ${side} order placed for ${symbol}${data.sandbox ? ' (TESTNET)' : ''}`, 'system');
      } catch (err: any) {
        console.error('Trade error:', err);
        get().addToast('Trade Error', err.message, 'rekt');
        return; // Stop if real trade fails
      }
    }

    let earnedPnl = 0;
    set((state) => {
      const p = { ...state.portfolio, assets: { ...state.portfolio.assets }, avgCost: { ...state.portfolio.avgCost } };
      const currentAssets = p.assets[symbol] || 0;
      const newTrades = [...state.tradeHistory];
      const id = `${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;

      if (side === "BUY") {
        if (p.usdt >= amountUsd) {
          const qty = amountUsd / price;
          const prevAvg = p.avgCost[symbol] || price;
          const totalQty = currentAssets + qty;
          p.avgCost[symbol] = (prevAvg * currentAssets + price * qty) / totalQty;
          p.usdt -= amountUsd;
          p.assets[symbol] = totalQty;
          newTrades.unshift({ id, symbol, side, quantity: qty, price, timestamp: Date.now() });
        }
      } else {
        const amountToSellTokens = amountUsd / price;
        if (currentAssets >= amountToSellTokens) {
          const avgCost = p.avgCost[symbol] || price;
          const pnl = (price - avgCost) * amountToSellTokens;
          earnedPnl = pnl;
          p.assets[symbol] = currentAssets - amountToSellTokens;
          p.usdt += amountUsd;
          newTrades.unshift({ id, symbol, side, quantity: amountToSellTokens, price, timestamp: Date.now(), pnl });
        }
      }
      
      return { portfolio: p, tradeHistory: newTrades.slice(0, 200) };
    });

    if (earnedPnl > 0) {
      get().addExp(earnedPnl * 10);
    }
  },

  toggleAudio: () => set((state) => ({ audioEnabled: !state.audioEnabled })),

  setDefiTVL: (data) => set({ defiTVL: data }),
  setNewsItems: (items) => set({ newsItems: items }),

  toggleAutoTrade: () => set((state) => ({ autoTradeEnabled: !state.autoTradeEnabled })),
  addAILog: (log) => set((state) => ({
    aiExecutionLogs: [{ ...log, id: Math.random().toString(36).substring(7) }, ...state.aiExecutionLogs].slice(0, 100),
  })),

  toggleRealMode: () => set((state) => ({ realModeEnabled: !state.realModeEnabled })),
  setApiKeys: (keys) => {
    set({ apiKeys: keys });
    if (typeof window !== 'undefined') {
      localStorage.setItem('binance_api_keys', JSON.stringify(keys));
    }
  },

  addExp: (amount) => set((state) => {
    let newExp = state.playerExp + amount;
    let newLevel = state.playerLevel;
    while (newExp >= newLevel * 1000) {
      newLevel++;
    }
    return { playerExp: newExp, playerLevel: newLevel };
  }),
  setTheme: (theme) => set({ currentTheme: theme }),
}));
