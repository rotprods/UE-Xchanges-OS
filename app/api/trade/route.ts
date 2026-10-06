import { NextResponse } from "next/server";
import ccxt from "ccxt";

export async function POST(request: Request) {
  try {
    // ─── Auth Check ──────────────────────────────────────────────────────
    const adminPassword = process.env.ADMIN_PASSWORD;
    if (adminPassword) {
      const authCookie = request.headers
        .get("cookie")
        ?.split(";")
        .find((c) => c.trim().startsWith("chronos_auth="));
      const token = authCookie?.split("=")[1]?.trim();
      if (token !== adminPassword) {
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
      }
    }

    // ─── Input Validation ────────────────────────────────────────────────
    const body = await request.json();
    const { symbol, side, amount } = body;

    if (!symbol || typeof symbol !== "string") {
      return NextResponse.json(
        { success: false, error: "Invalid symbol" },
        { status: 400 }
      );
    }
    if (!side || !["BUY", "SELL", "buy", "sell"].includes(side)) {
      return NextResponse.json(
        { success: false, error: "Invalid side (must be BUY or SELL)" },
        { status: 400 }
      );
    }
    if (!amount || typeof amount !== "number" || amount <= 0) {
      return NextResponse.json(
        { success: false, error: "Invalid amount" },
        { status: 400 }
      );
    }

    // ─── Exchange Keys (SERVER-SIDE ONLY) ────────────────────────────────
    const apiKey = process.env.BINANCE_API_KEY;
    const secret = process.env.BINANCE_SECRET;

    if (!apiKey || !secret) {
      return NextResponse.json(
        {
          success: false,
          error: "Exchange API keys not configured on server",
        },
        { status: 500 }
      );
    }

    // ─── Initialize Exchange ─────────────────────────────────────────────
    const exchange = new ccxt.binance({
      apiKey,
      secret,
      enableRateLimit: true,
    });

    // Sandbox mode controlled by env var (defaults to true for safety)
    const isSandbox = process.env.BINANCE_SANDBOX !== "false";
    exchange.setSandboxMode(isSandbox);

    // Format symbol from 'BTCUSDT' to 'BTC/USDT'
    const formattedSymbol = symbol.includes("/")
      ? symbol
      : symbol.replace("USDT", "/USDT");

    // ─── Execute Trade ───────────────────────────────────────────────────
    const orderSide = side.toLowerCase() as "buy" | "sell";
    const order = await exchange.createMarketOrder(
      formattedSymbol,
      orderSide,
      amount
    );

    // ─── Structured Logging ──────────────────────────────────────────────
    console.log(
      JSON.stringify({
        event: "TRADE_EXECUTED",
        symbol: formattedSymbol,
        side: orderSide,
        amount,
        sandbox: isSandbox,
        orderId: order.id,
        timestamp: new Date().toISOString(),
      })
    );

    return NextResponse.json({ success: true, order, sandbox: isSandbox });
  } catch (error: any) {
    console.error("Trade execution error:", error);
    return NextResponse.json(
      { success: false, error: error.message || "Trade execution failed" },
      { status: 500 }
    );
  }
}
