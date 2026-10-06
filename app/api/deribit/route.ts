import { NextResponse } from "next/server";

// In-memory cache
let cache: { data: any; timestamp: number } | null = null;
const CACHE_TTL_MS = 5000; // 5 seconds

export async function GET() {
  // Return cached data if fresh
  if (cache && Date.now() - cache.timestamp < CACHE_TTL_MS) {
    return NextResponse.json(cache.data, {
      headers: {
        "Cache-Control": "s-maxage=5, stale-while-revalidate=10",
      },
    });
  }

  try {
    const res = await fetch(
      "https://test.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option",
      { next: { revalidate: 5 } }
    );
    const data = await res.json();

    // Update cache
    cache = { data, timestamp: Date.now() };

    return NextResponse.json(data, {
      headers: {
        "Cache-Control": "s-maxage=5, stale-while-revalidate=10",
      },
    });
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to fetch from Deribit" },
      { status: 500 }
    );
  }
}
