import * as Comlink from "comlink";

interface TickerData {
  symbol: string;
  price: string;
  open: string;
  high: string;
  low: string;
  volume: string;
  volumeQuote: string;
}

interface MempoolEvent {
  hash: string;
  network: string;
  gas: number;
  value: string;
  time: number;
}

class TickerWorker {
  private ws: WebSocket | null = null;
  private klineWs: WebSocket | null = null;
  private depthWs: WebSocket | null = null;
  private futuresWs: WebSocket | null = null;
  private aggTradeWs: WebSocket | null = null;
  
  private klineSimInterval: NodeJS.Timeout | null = null;
  private depthSimInterval: NodeJS.Timeout | null = null;
  private mempoolInterval: NodeJS.Timeout | null = null;
  private defiInterval: NodeJS.Timeout | null = null;
  private newsInterval: NodeJS.Timeout | null = null;
  
  private currentKlineSymbol: string = "BTCUSDT";
  private currentKlineInterval: string = "1m";
  private marketMode: "CRYPTO" | "STOCKS" = "CRYPTO";
  
  private onDataCallback: ((data: any) => void) | null = null;
  
  private watchedCrypto = new Set([
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", 
    "DOGEUSDT", "ADAUSDT", "TRXUSDT", "TONUSDT", "LINKUSDT",
    "HBARUSDT", "XLMUSDT"
  ]);

  private watchedStocks = new Set([
    "NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "SPY", "GME", "AMC"
  ]);

  private stockBasePrices: Record<string, number> = {
    NVDA: 120.40, TSLA: 175.50, AAPL: 185.20, MSFT: 420.10, 
    AMZN: 180.30, SPY: 520.40, GME: 25.10, AMC: 4.80
  };

  private tickerStore: Record<string, TickerData> = {};
  
  private stats = {
    totalVolume24h: 0,
    txsPerSecond: 0,
    gasGwei: 10, // Will be updated by real mempool
    lastUpdate: Date.now(),
  };
  private txCounter = 0;
  private tpsInterval: NodeJS.Timeout | null = null;

  constructor() {
    this.watchedStocks.forEach(sym => {
      const base = this.stockBasePrices[sym];
      this.tickerStore[sym] = {
        symbol: sym,
        price: base.toFixed(2),
        open: base.toFixed(2),
        high: base.toFixed(2),
        low: base.toFixed(2),
        volume: (Math.random() * 1000000 + 500000).toFixed(2),
        volumeQuote: (Math.random() * 100000000 + 50000000).toFixed(2)
      };
    });

    this.tpsInterval = setInterval(() => {
      this.stats.txsPerSecond = this.txCounter;
      this.txCounter = 0;
      this.flush();
    }, 1000);

    // Brownian Motion for Stocks
    setInterval(() => {
      if (this.marketMode !== "STOCKS") return;
      this.watchedStocks.forEach(sym => {
        const ticker = this.tickerStore[sym];
        const currentPrice = parseFloat(ticker.price);
        const volatility = sym === "GME" || sym === "AMC" ? 0.005 : 0.001;
        const change = currentPrice * (Math.random() * volatility * 2 - volatility);
        const newPrice = currentPrice + change;
        
        ticker.price = newPrice.toFixed(2);
        ticker.high = Math.max(parseFloat(ticker.high), newPrice).toFixed(2);
        ticker.low = Math.min(parseFloat(ticker.low), newPrice).toFixed(2);
        ticker.volume = (parseFloat(ticker.volume) + Math.random() * 100).toFixed(2);
        ticker.volumeQuote = (parseFloat(ticker.volumeQuote) + Math.random() * 10000).toFixed(2);
        
        this.txCounter++;
        this.stats.totalVolume24h += Math.random() * 10000;
      });
      this.flush();
    }, 400);

    // Real Mempool.space Polling (every 10s)
    const fetchMempool = async () => {
      if (this.marketMode !== "CRYPTO") return;
      try {
        const res = await fetch("https://mempool.space/api/v1/fees/recommended");
        const json = await res.json();
        if (json.fastestFee) {
          this.stats.gasGwei = json.fastestFee;
          
          // Dispatch fake mempool event just for the visual radar but with real fees
          if (this.onDataCallback) {
             const mockEvent: MempoolEvent = {
              hash: "0x" + Array.from({ length: 16 }, () => Math.floor(Math.random() * 16).toString(16)).join(""),
              network: "Bitcoin",
              gas: json.fastestFee,
              value: (Math.random() * 2).toFixed(4),
              time: Date.now()
            };
            this.onDataCallback({ mempoolEvent: mockEvent });
          }
        }
      } catch (e) {
        // Silent fail
      }
    };
    fetchMempool();
    this.mempoolInterval = setInterval(fetchMempool, 10000);

    // DefiLlama polling — every 60s
    const fetchDefiData = async () => {
      try {
        const [globalRes, chainsRes] = await Promise.all([
          fetch('https://api.llama.fi/v2/globalCharts'),
          fetch('https://api.llama.fi/v2/chains'),
        ]);
        if (!globalRes.ok || !chainsRes.ok) return;

        const globalData: Array<[number, number]> = await globalRes.json();
        const chainsData: Array<{ name: string; tvl: number; change1d?: number; change_1d?: number }> = await chainsRes.json();

        let tvl = 0;
        let change24h = 0;
        if (Array.isArray(globalData) && globalData.length >= 2) {
          const latest = globalData[globalData.length - 1];
          const prev = globalData[globalData.length - 2];
          tvl = latest[1];
          const prevTvl = prev[1];
          change24h = prevTvl > 0 ? ((tvl - prevTvl) / prevTvl) * 100 : 0;
        }

        const sortedChains = [...chainsData]
          .sort((a, b) => (b.tvl ?? 0) - (a.tvl ?? 0))
          .slice(0, 5)
          .map((c) => ({
            name: c.name,
            tvl: c.tvl ?? 0,
            change24h: c.change1d ?? c.change_1d ?? 0,
          }));

        if (this.onDataCallback) {
          this.onDataCallback({
            defiData: { total: tvl, change24h, chains: sortedChains },
          });
        }
      } catch {
        // silent fail
      }
    };
    fetchDefiData();
    this.defiInterval = setInterval(fetchDefiData, 60000);

    // CryptoCompare news polling — every 120s
    const fetchNewsData = async () => {
      try {
        const res = await fetch(
          'https://min-api.cryptocompare.com/data/v2/news/?lang=EN&sortOrder=latest'
        );
        if (!res.ok) return;
        const json = await res.json();
        const articles: any[] = json.Data ?? [];
        const newsItems = articles.slice(0, 10).map((item: any) => ({
          id: String(item.id),
          title: item.title ?? '',
          body: item.body ?? '',
          url: item.url ?? '',
          source: item.source_info?.name ?? item.source ?? 'Unknown',
          publishedAt: item.published_on ?? 0,
          categories: item.categories ?? '',
          imageUrl: item.imageurl ?? '',
        }));
        if (this.onDataCallback) {
          this.onDataCallback({ newsData: newsItems });
        }
      } catch {
        // silent fail
      }
    };
    fetchNewsData();
    this.newsInterval = setInterval(fetchNewsData, 120000);
  }

  public registerCallback(cb: (data: any) => void) {
    this.onDataCallback = cb;
  }

  public setMarketMode(mode: "CRYPTO" | "STOCKS") {
    this.marketMode = mode;
    this.reconnectDepthStream();
  }

  public start() {
    if (this.ws) return;
    
    // 1. MiniTicker (Global Prices)
    this.ws = new WebSocket("wss://stream.binance.com:9443/ws/!miniTicker@arr");
    this.ws.onmessage = (event) => {
      const rawData = JSON.parse(event.data);
      if (!Array.isArray(rawData)) return;

      let dataChanged = false;
      let totalVolQuote = 0;

      rawData.forEach((item: any) => {
        const symbol = item.s;
        if (this.marketMode === "CRYPTO") this.txCounter++;

        if (this.watchedCrypto.has(symbol)) {
          this.tickerStore[symbol] = {
            symbol,
            price: parseFloat(item.c).toFixed(2),
            open: parseFloat(item.o).toFixed(2),
            high: parseFloat(item.h).toFixed(2),
            low: parseFloat(item.l).toFixed(2),
            volume: parseFloat(item.v).toFixed(2),
            volumeQuote: parseFloat(item.q).toFixed(2),
          };
          dataChanged = true;
        }
        totalVolQuote += parseFloat(item.q || 0);
      });

      if (this.marketMode === "CRYPTO") {
        this.stats.totalVolume24h = Math.round(totalVolQuote);
        this.stats.lastUpdate = Date.now();
        if (dataChanged) this.flush();
      }
    };

    // 2. Liquidations WS (Futures)
    try {
      this.futuresWs = new WebSocket("wss://fstream.binance.com/ws/!forceOrder@arr");
      this.futuresWs.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.e === "forceOrder" && this.marketMode === "CRYPTO" && this.onDataCallback) {
          const order = data.o;
          const symbol = order.s;
          const side = order.S; // "SELL" or "BUY" -> if "SELL", means LONG was liquidated. If "BUY", SHORT was liquidated.
          const amount = parseFloat(order.q);
          const price = parseFloat(order.p);
          const value = amount * price;

          if (value > 20000) { // Only show liquidations > $20k to avoid spam
            const rektSide = side === "SELL" ? "LONG" : "SHORT";
            this.onDataCallback({
              rektAlert: {
                side: rektSide,
                message: `${symbol} $${value.toLocaleString(undefined, { maximumFractionDigits: 0 })} REKT`,
              }
            });
          }
        }
      };
    } catch(e) {}

    // 3. Real Whale Alerts (AggTrade)
    try {
      this.aggTradeWs = new WebSocket("wss://stream.binance.com:9443/ws/btcusdt@aggTrade/ethusdt@aggTrade/solusdt@aggTrade");
      this.aggTradeWs.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.e === "aggTrade" && this.marketMode === "CRYPTO" && this.onDataCallback) {
          const price = parseFloat(data.p);
          const qty = parseFloat(data.q);
          const valueUsd = price * qty;
          
          if (valueUsd > 150000) { // Whale detected: Trade > $150k
            const isBuy = data.m; // m = true if buyer is market maker (so it was a sell)
            const action = isBuy ? "MARKET SELL" : "MARKET BUY";
            const token = data.s.replace("USDT", "");
            
            this.onDataCallback({
              whaleAlert: {
                id: "WHL-" + data.a,
                token: token,
                amountUsd: valueUsd.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }),
                from: action,
                to: "Binance Spot",
                time: Date.now()
              }
            });
          }
        }
      };
    } catch(e) {}

    this.connectKlineWs(this.currentKlineSymbol, this.currentKlineInterval);
    this.reconnectDepthStream();
  }

  private reconnectDepthStream() {
    if (this.depthWs) {
      this.depthWs.close();
      this.depthWs = null;
    }
    if (this.depthSimInterval) {
      clearInterval(this.depthSimInterval);
      this.depthSimInterval = null;
    }

    if (this.marketMode === "CRYPTO") {
      try {
        this.depthWs = new WebSocket("wss://stream.binance.com:9443/ws/btcusdt@depth20@100ms");
        this.depthWs.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.bids && data.asks && this.onDataCallback) {
            const parsedBids = data.bids.map((b: any) => ({ price: parseFloat(b[0]), size: parseFloat(b[1]) }));
            const parsedAsks = data.asks.map((a: any) => ({ price: parseFloat(a[0]), size: parseFloat(a[1]) }));
            this.onDataCallback({ orderBook: { bids: parsedBids, asks: parsedAsks } });
          }
        };
      } catch (err) {
        console.error("Failed to connect Depth WS", err);
      }
    } else {
      // Simulate OrderBook for Stocks
      this.depthSimInterval = setInterval(() => {
        let basePrice = 65000;
        if (this.tickerStore["NVDA"]) {
          basePrice = parseFloat(this.tickerStore["NVDA"].price);
        }
        const spread = basePrice * 0.0005;
        const bids = Array.from({ length: 20 }, (_, i) => ({
          price: basePrice - (i * spread) - Math.random() * spread,
          size: Math.random() * 50 + (20 - i) * 5,
        }));
        const asks = Array.from({ length: 20 }, (_, i) => ({
          price: basePrice + (i * spread) + Math.random() * spread,
          size: Math.random() * 50 + (20 - i) * 5,
        }));

        if (this.onDataCallback) {
          this.onDataCallback({ orderBook: { bids, asks } });
        }
      }, 500);
    }
  }

  private connectKlineWs(symbol: string, interval: string) {
    if (this.klineWs) {
      this.klineWs.close();
      this.klineWs = null;
    }
    if (this.klineSimInterval) {
      clearInterval(this.klineSimInterval);
      this.klineSimInterval = null;
    }

    this.currentKlineSymbol = symbol;
    this.currentKlineInterval = interval;

    if (this.watchedCrypto.has(symbol)) {
      try {
        const streamUrl = `wss://stream.binance.com:9443/ws/${symbol.toLowerCase()}@kline_${interval}`;
        this.klineWs = new WebSocket(streamUrl);
        this.klineWs.onmessage = (event) => {
          const message = JSON.parse(event.data);
          const k = message.k;
          if (k && this.onDataCallback) {
            this.onDataCallback({ latestCandle: {
              time: Math.floor(k.t / 1000),
              open: parseFloat(k.o),
              high: parseFloat(k.h),
              low: parseFloat(k.l),
              close: parseFloat(k.c),
            }});
          }
        };
      } catch (e) {
        console.error("Failed to initialize Kline WebSocket", e);
      }
    } else if (this.watchedStocks.has(symbol)) {
      let currentCandle: any = null;
      let lastCandleTime = 0;

      this.klineSimInterval = setInterval(() => {
        const nowSec = Math.floor(Date.now() / 1000);
        let intervalSecs = 60;
        if (interval === "1s") intervalSecs = 1;
        if (interval === "15m") intervalSecs = 900;
        if (interval === "1h") intervalSecs = 3600;
        if (interval === "4h") intervalSecs = 14400;
        if (interval === "1d") intervalSecs = 86400;
        if (interval === "1w") intervalSecs = 604800;
        if (interval === "1M") intervalSecs = 2592000;

        const candleTime = nowSec - (nowSec % intervalSecs);
        const ticker = this.tickerStore[symbol];
        const currentPrice = parseFloat(ticker.price);

        if (!currentCandle || candleTime > lastCandleTime) {
          currentCandle = { time: candleTime, open: currentPrice, high: currentPrice, low: currentPrice, close: currentPrice };
          lastCandleTime = candleTime;
        } else {
          currentCandle.high = Math.max(currentCandle.high, currentPrice);
          currentCandle.low = Math.min(currentCandle.low, currentPrice);
          currentCandle.close = currentPrice;
        }

        if (this.onDataCallback) {
          this.onDataCallback({ latestCandle: { ...currentCandle } });
        }
      }, 1000);
    }
  }

  public setKlineConfig(symbol: string, interval: string) {
    this.connectKlineWs(symbol, interval);
  }

  public stop() {
    if (this.ws) { this.ws.close(); this.ws = null; }
    if (this.klineWs) { this.klineWs.close(); this.klineWs = null; }
    if (this.depthWs) { this.depthWs.close(); this.depthWs = null; }
    if (this.futuresWs) { this.futuresWs.close(); this.futuresWs = null; }
    if (this.aggTradeWs) { this.aggTradeWs.close(); this.aggTradeWs = null; }
    
    if (this.klineSimInterval) { clearInterval(this.klineSimInterval); this.klineSimInterval = null; }
    if (this.depthSimInterval) { clearInterval(this.depthSimInterval); this.depthSimInterval = null; }
    if (this.mempoolInterval) { clearInterval(this.mempoolInterval); this.mempoolInterval = null; }
    if (this.defiInterval) { clearInterval(this.defiInterval); this.defiInterval = null; }
    if (this.newsInterval) { clearInterval(this.newsInterval); this.newsInterval = null; }
    if (this.tpsInterval) { clearInterval(this.tpsInterval); this.tpsInterval = null; }
  }

  private flush() {
    if (this.onDataCallback) {
      const filteredTickers: Record<string, TickerData> = {};
      const targetSet = this.marketMode === "CRYPTO" ? this.watchedCrypto : this.watchedStocks;
      for (const [sym, data] of Object.entries(this.tickerStore)) {
        if (targetSet.has(sym)) filteredTickers[sym] = data;
      }
      this.onDataCallback({
        tickers: filteredTickers,
        stats: { ...this.stats },
      });
    }
  }
}

Comlink.expose(TickerWorker);
export type { TickerData, MempoolEvent };
export { TickerWorker };
