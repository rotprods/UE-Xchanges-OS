import { NextResponse } from "next/server";

// In-memory cache for arbitrage data
let cache: { data: any; timestamp: number } | null = null;
const CACHE_TTL_MS = 2000; // 2 seconds

export async function GET() {
  // Return cached data if still fresh
  if (cache && Date.now() - cache.timestamp < CACHE_TTL_MS) {
    return NextResponse.json(cache.data);
  }

  try {
    const [binanceRes, coinbaseRes, krakenRes] = await Promise.allSettled([
      fetch("https://api.binance.com/api/v3/ticker/bookTicker?symbol=BTCUSDT"),
      fetch("https://api.exchange.coinbase.com/products/BTC-USD/ticker"),
      fetch("https://api.kraken.com/0/public/Ticker?pair=XBTUSD"),
    ]);

    const exchanges: { name: string; bid: number; ask: number }[] = [];

    if (binanceRes.status === "fulfilled" && binanceRes.value.ok) {
      const data = await binanceRes.value.json();
      exchanges.push({
        name: "Binance",
        bid: parseFloat(data.bidPrice || "0"),
        ask: parseFloat(data.askPrice || "0"),
      });
    }

    if (coinbaseRes.status === "fulfilled" && coinbaseRes.value.ok) {
      const data = await coinbaseRes.value.json();
      exchanges.push({
        name: "Coinbase",
        bid: parseFloat(data.bid || "0"),
        ask: parseFloat(data.ask || "0"),
      });
    }

    if (krakenRes.status === "fulfilled" && krakenRes.value.ok) {
      const data = await krakenRes.value.json();
      exchanges.push({
        name: "Kraken",
        bid: parseFloat(data.result?.XXBTZUSD?.b?.[0] || "0"),
        ask: parseFloat(data.result?.XXBTZUSD?.a?.[0] || "0"),
      });
    }

    const result = { exchanges, timestamp: Date.now() };

    // Update cache
    cache = { data: result, timestamp: Date.now() };

    return NextResponse.json(result);
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to fetch exchange data" },
      { status: 500 }
    );
  }
}
