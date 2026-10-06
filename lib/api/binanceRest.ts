/**
 * Binance REST API client for historical kline (candlestick) data.
 *
 * Fetches from the public endpoint — no API key required.
 * Maps the raw array response to the CandleData interface.
 */

export interface CandleData {
  time: number | string;
  open: number;
  high: number;
  low: number;
  close: number;
}

/**
 * Fetch historical klines from Binance.
 *
 * @param symbol   - Trading pair, e.g. "BTCUSDT"
 * @param interval - Kline interval, e.g. "1h", "4h", "1d"
 * @param limit    - Number of candles to fetch (max 1000, default 500)
 * @returns Array of CandleData with time in **seconds** (Unix epoch)
 */
export async function fetchHistoricalKlines(
  symbol: string,
  interval: string,
  limit: number = 500
): Promise<CandleData[]> {
  const url = new URL("https://api.binance.com/api/v3/klines");
  url.searchParams.set("symbol", symbol.toUpperCase());
  url.searchParams.set("interval", interval);
  url.searchParams.set("limit", String(Math.min(limit, 1000)));

  const response = await fetch(url.toString());

  if (!response.ok) {
    const body = await response.text();
    throw new Error(
      `Binance API error ${response.status}: ${body}`
    );
  }

  /*
   * Binance kline array format (per element):
   * [0]  Open time (ms)
   * [1]  Open
   * [2]  High
   * [3]  Low
   * [4]  Close
   * [5]  Volume
   * [6]  Close time (ms)
   * [7]  Quote asset volume
   * [8]  Number of trades
   * [9]  Taker buy base asset volume
   * [10] Taker buy quote asset volume
   * [11] Unused
   */
  const raw: unknown[][] = await response.json();

  return raw.map((k) => ({
    time: Math.floor(Number(k[0]) / 1000), // ms → seconds
    open: parseFloat(k[1] as string),
    high: parseFloat(k[2] as string),
    low: parseFloat(k[3] as string),
    close: parseFloat(k[4] as string),
  }));
}
