/**
 * Cron endpoint — Takes a market snapshot for all tracked symbols.
 * 
 * Called every 5 minutes by Vercel Cron or an external scheduler.
 * Saves snapshots to the database for AI training.
 * 
 * URL: POST /api/cron/snapshot
 * Auth: Requires CRON_SECRET header
 */

import { NextRequest, NextResponse } from "next/server";
import { buildSnapshot, type MarketSnapshotData } from "../../../../lib/pipeline/SnapshotBuilder";

// Symbols to track (same as the worker's watchedCrypto set)
const TRACKED_SYMBOLS = [
  "BTCUSDT",
  "ETHUSDT",
  "SOLUSDT",
  "BNBUSDT",
  "XRPUSDT",
];

export async function POST(request: NextRequest) {
  // Verify cron secret
  const authHeader = request.headers.get("authorization");
  const cronSecret = process.env.CRON_SECRET;
  if (cronSecret && authHeader !== `Bearer ${cronSecret}`) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const snapshots: MarketSnapshotData[] = [];
    const errors: string[] = [];

    // Build snapshots for all tracked symbols in parallel
    const results = await Promise.allSettled(
      TRACKED_SYMBOLS.map((symbol) => buildSnapshot(symbol))
    );

    results.forEach((result, i) => {
      if (result.status === "fulfilled") {
        snapshots.push(result.value);
      } else {
        errors.push(`${TRACKED_SYMBOLS[i]}: ${result.reason}`);
      }
    });

    // Attempt to save to DB if available (Supabase preferred, Drizzle fallback)
    let dbSaved = false;
    try {
      const { insertSnapshot, isSupabaseConfigured } = await import("../../../../lib/db/supabase");
      if (isSupabaseConfigured()) {
        for (const snapshot of snapshots) {
          await insertSnapshot({
            timestamp: snapshot.timestamp,
            symbol: snapshot.symbol,
            price: snapshot.price,
            open: snapshot.open,
            high: snapshot.high,
            low: snapshot.low,
            volume_24h: snapshot.volume24h,
            rsi_14: snapshot.rsi14,
            sma_7: snapshot.sma7,
            sma_25: snapshot.sma25,
            sma_99: snapshot.sma99,
            ema_21: snapshot.ema21,
            macd_line: snapshot.macdLine,
            macd_signal: snapshot.macdSignal,
            macd_histogram: snapshot.macdHistogram,
            bb_upper: snapshot.bbUpper,
            bb_lower: snapshot.bbLower,
            bb_width: snapshot.bbWidth,
            vwap: snapshot.vwap,
            adx: snapshot.adx,
            obv: snapshot.obv,
            atr_14: snapshot.atr14,
            trend_direction: snapshot.trendDirection,
            trend_strength: snapshot.trendStrength,
            btc_mempool_fee: snapshot.btcMempoolFee,
            funding_rate: snapshot.fundingRate,
            open_interest: snapshot.openInterest,
            fear_greed_index: snapshot.fearGreedIndex,
            defi_tvl: snapshot.defiTvl,
            graph_signal_score: snapshot.graphSignalScore,
            graph_confidence: snapshot.graphConfidence,
            graph_direction: snapshot.graphDirection,
          });
        }
        dbSaved = true;
      }
    } catch (dbErr: any) {
      errors.push(`DB save failed: ${dbErr.message}`);
    }

    return NextResponse.json({
      success: true,
      snapshotsCount: snapshots.length,
      dbSaved,
      errors: errors.length > 0 ? errors : undefined,
      timestamp: Date.now(),
      symbols: snapshots.map((s) => ({
        symbol: s.symbol,
        price: s.price,
        rsi: s.rsi14?.toFixed(1),
        trend: s.trendDirection,
        fearGreed: s.fearGreedIndex,
        fundingRate: s.fundingRate?.toFixed(6),
        signalScore: s.graphSignalScore,
      })),
    });
  } catch (err: any) {
    return NextResponse.json(
      { error: err.message || "Snapshot failed" },
      { status: 500 }
    );
  }
}

// Also support GET for easy testing
export async function GET(request: NextRequest) {
  return POST(request);
}
