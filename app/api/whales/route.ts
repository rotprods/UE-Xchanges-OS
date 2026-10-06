import { NextResponse } from "next/server";

// In-memory store for recent whale alerts detected by polling
let recentWhales: any[] = [];
let lastBlockChecked = 0;

export async function GET() {
  // Return the most recent whale alerts
  // In production with a DB, this would query the whale_alerts table
  return NextResponse.json({
    whales: recentWhales.slice(0, 20),
    lastBlock: lastBlockChecked,
    timestamp: Date.now(),
  });
}

// POST endpoint called by a cron job or external service to push whale data
export async function POST(request: Request) {
  try {
    const adminPassword = process.env.ADMIN_PASSWORD;
    if (adminPassword) {
      const authHeader = request.headers.get("authorization");
      if (authHeader !== `Bearer ${adminPassword}`) {
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
      }
    }

    const body = await request.json();
    const { hash, amount, from, to, symbol, blockNumber } = body;

    if (amount && amount >= 1000000) {
      const alert = {
        id: `WHL-${Date.now()}`,
        hash,
        token: symbol || "USDT",
        amountUsd: `$${Number(amount).toLocaleString("en-US", { maximumFractionDigits: 0 })}`,
        from: from ? `${from.slice(0, 6)}...${from.slice(-4)}` : "Unknown",
        to: to ? `${to.slice(0, 6)}...${to.slice(-4)}` : "Unknown",
        time: Date.now(),
      };

      recentWhales = [alert, ...recentWhales].slice(0, 50);
      if (blockNumber) lastBlockChecked = blockNumber;
    }

    return NextResponse.json({ success: true });
  } catch {
    return NextResponse.json({ error: "Invalid request" }, { status: 400 });
  }
}
