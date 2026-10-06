import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { portfolios } from "@/lib/db/schema";
import { eq } from "drizzle-orm";

// ─── In-Memory Defaults ──────────────────────────────────────────────────────
const DEFAULT_PORTFOLIO = {
  usdt: 1_000_000,
  assets: {} as Record<string, number>,
  avgCost: {} as Record<string, number>,
};

// In-memory state used when no DB is configured
let memoryPortfolio = { ...DEFAULT_PORTFOLIO };

// Default user ID (simple auth — single admin user)
const DEFAULT_USER_ID = 1;

// ─── GET /api/portfolio ──────────────────────────────────────────────────────
export async function GET() {
  try {
    // Try database first
    if (db) {
      const rows = await db
        .select()
        .from(portfolios)
        .where(eq(portfolios.userId, DEFAULT_USER_ID))
        .limit(1);

      if (rows.length > 0) {
        const row = rows[0];
        return NextResponse.json({
          usdt: row.usdt,
          assets: row.assets,
          avgCost: row.avgCost,
        });
      }
    }

    // Fallback to in-memory defaults
    return NextResponse.json(memoryPortfolio);
  } catch (error: unknown) {
    console.error("[portfolio] GET error:", error);
    // Even on DB failure, return the in-memory fallback
    return NextResponse.json(memoryPortfolio);
  }
}

// ─── PUT /api/portfolio ──────────────────────────────────────────────────────
export async function PUT(request: Request) {
  try {
    const body = await request.json();
    const { usdt, assets, avgCost } = body;

    // Validate input
    if (usdt !== undefined && typeof usdt !== "number") {
      return NextResponse.json(
        { error: "usdt must be a number" },
        { status: 400 }
      );
    }

    const update = {
      ...(usdt !== undefined && { usdt }),
      ...(assets !== undefined && { assets }),
      ...(avgCost !== undefined && { avgCost }),
      updatedAt: new Date(),
    };

    // Try database first
    if (db) {
      const existing = await db
        .select()
        .from(portfolios)
        .where(eq(portfolios.userId, DEFAULT_USER_ID))
        .limit(1);

      if (existing.length > 0) {
        await db
          .update(portfolios)
          .set(update)
          .where(eq(portfolios.userId, DEFAULT_USER_ID));
      } else {
        await db.insert(portfolios).values({
          userId: DEFAULT_USER_ID,
          usdt: usdt ?? DEFAULT_PORTFOLIO.usdt,
          assets: assets ?? DEFAULT_PORTFOLIO.assets,
          avgCost: avgCost ?? DEFAULT_PORTFOLIO.avgCost,
          updatedAt: new Date(),
        });
      }

      return NextResponse.json({ success: true, ...update });
    }

    // Fallback: update in-memory state
    if (usdt !== undefined) memoryPortfolio.usdt = usdt;
    if (assets !== undefined) memoryPortfolio.assets = assets;
    if (avgCost !== undefined) memoryPortfolio.avgCost = avgCost;

    return NextResponse.json({ success: true, ...memoryPortfolio });
  } catch (error: unknown) {
    console.error("[portfolio] PUT error:", error);
    return NextResponse.json(
      { error: "Failed to update portfolio" },
      { status: 500 }
    );
  }
}
