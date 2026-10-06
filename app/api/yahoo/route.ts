import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const symbol = searchParams.get('symbol');
  let interval = searchParams.get('interval') || '1m';
  
  if (!symbol) {
    return NextResponse.json({ error: "Missing symbol" }, { status: 400 });
  }

  // Map Binance intervals to Yahoo Finance intervals
  const intervalMap: Record<string, string> = {
    '1s': '1m', // Yahoo doesn't support 1s, fallback to 1m
    '1m': '1m',
    '15m': '15m',
    '1h': '60m',
    '4h': '60m', // Yahoo doesn't support 4h well without pro, fallback or fetch 60m and aggregate. We'll fallback to 60m for now.
    '1d': '1d',
    '1w': '1wk',
    '1M': '1mo'
  };

  const yfInterval = intervalMap[interval] || '1m';
  
  // Choose range based on interval to ensure we get enough data
  let range = '5d';
  if (['1d', '1wk', '1mo'].includes(yfInterval)) range = '2y';
  if (['60m'].includes(yfInterval)) range = '1mo';

  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${symbol}?interval=${yfInterval}&range=${range}`;

  try {
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
      }
    });

    if (!response.ok) {
      throw new Error(`Yahoo Finance API responded with status: ${response.status}`);
    }

    const data = await response.json();
    const result = data.chart?.result?.[0];

    if (!result || !result.timestamp) {
      return NextResponse.json([], { status: 200 }); // Return empty if no data
    }

    const timestamps = result.timestamp;
    const quote = result.indicators.quote[0];

    // Format to look like Binance Klines: [timeMs, open, high, low, close, volume]
    const formattedData = [];
    for (let i = 0; i < timestamps.length; i++) {
      if (quote.open[i] !== null && quote.close[i] !== null) {
        formattedData.push([
          timestamps[i] * 1000, // s to ms
          quote.open[i],
          quote.high[i],
          quote.low[i],
          quote.close[i],
          quote.volume[i] || 0
        ]);
      }
    }

    // Limit to 150 items to match the Binance logic
    return NextResponse.json(formattedData.slice(-150));
  } catch (error: any) {
    console.error("Yahoo API Proxy Error:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
