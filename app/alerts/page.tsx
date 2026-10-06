"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useOmniStore } from "../../store/omniStore";

interface AlertConfig {
  id: string;
  symbol: string;
  condition: "ABOVE" | "BELOW";
  price: number;
  triggered: boolean;
  createdAt: number;
}

export default function AlertsPage() {
  const tickers = useOmniStore((state) => state.tickers);
  const addToast = useOmniStore((state) => state.addToast);
  const marketMode = useOmniStore((state) => state.marketMode);

  const [alerts, setAlerts] = useState<AlertConfig[]>([]);
  const [newSymbol, setNewSymbol] = useState("BTCUSDT");
  const [newCondition, setNewCondition] = useState<"ABOVE" | "BELOW">("ABOVE");
  const [newPrice, setNewPrice] = useState<string>("");

  const symbols = marketMode === "CRYPTO"
    ? ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "TRXUSDT"]
    : ["NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "SPY"];

  // Check alerts
  React.useEffect(() => {
    const interval = setInterval(() => {
      setAlerts((prev) =>
        prev.map((alert) => {
          if (alert.triggered) return alert;
          const ticker = tickers[alert.symbol];
          if (!ticker) return alert;
          const currentPrice = parseFloat(ticker.price);
          const shouldTrigger =
            (alert.condition === "ABOVE" && currentPrice >= alert.price) ||
            (alert.condition === "BELOW" && currentPrice <= alert.price);
          
          if (shouldTrigger) {
            addToast(
              "ALERT TRIGGERED",
              `${alert.symbol} is ${alert.condition} $${alert.price.toLocaleString()}`,
              "system"
            );
            // Browser notification
            if ("Notification" in window && Notification.permission === "granted") {
              new Notification(`Chronos Quantum Alert`, {
                body: `${alert.symbol} is ${alert.condition} $${alert.price.toLocaleString()}`,
              });
            }
            return { ...alert, triggered: true };
          }
          return alert;
        })
      );
    }, 1000);
    return () => clearInterval(interval);
  }, [tickers, addToast]);

  const createAlert = () => {
    const price = parseFloat(newPrice);
    if (isNaN(price) || price <= 0) return;

    const newAlert: AlertConfig = {
      id: Math.random().toString(36).substring(7),
      symbol: newSymbol,
      condition: newCondition,
      price,
      triggered: false,
      createdAt: Date.now(),
    };
    setAlerts((prev) => [newAlert, ...prev]);
    setNewPrice("");
  };

  const deleteAlert = (id: string) => {
    setAlerts((prev) => prev.filter((a) => a.id !== id));
  };

  const requestNotificationPermission = () => {
    if ("Notification" in window) {
      Notification.requestPermission();
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="font-orbitron text-xl text-[#00F0FF] font-bold tracking-wider">ALERT COMMANDER</h2>
          <p className="font-mono text-[10px] text-[rgba(255,255,255,0.4)] mt-1">Set price alerts with real-time monitoring</p>
        </div>
        <button
          onClick={requestNotificationPermission}
          className="text-[9px] font-mono text-[rgba(0,240,255,0.6)] hover:text-[#00F0FF] transition-colors px-3 py-2 border border-[rgba(0,240,255,0.2)] rounded-lg bg-[rgba(0,240,255,0.05)]"
        >
          ENABLE NOTIFICATIONS
        </button>
      </div>

      {/* Alert Builder */}
      <div className="border border-[rgba(0,240,255,0.3)] bg-[rgba(5,15,25,0.4)] backdrop-blur-md rounded-2xl p-6">
        <h3 className="font-orbitron text-[10px] tracking-widest text-[#00F0FF] font-bold mb-4 flex items-center">
          <span className="w-1.5 h-1.5 bg-[#00F0FF] rounded-full mr-2 animate-pulse" />
          CREATE NEW ALERT
        </h3>
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <span className="block font-mono text-[9px] text-[rgba(255,255,255,0.4)] mb-1">ASSET</span>
            <select
              value={newSymbol}
              onChange={(e) => setNewSymbol(e.target.value)}
              className="bg-[rgba(0,240,255,0.05)] border border-[rgba(0,240,255,0.3)] text-[#00F0FF] font-mono text-xs px-3 py-2 rounded-lg outline-none"
            >
              {symbols.map((s) => (
                <option key={s} value={s} className="bg-[#0A0A14] text-white">{s.replace("USDT", "")}</option>
              ))}
            </select>
          </div>
          <div>
            <span className="block font-mono text-[9px] text-[rgba(255,255,255,0.4)] mb-1">WHEN PRICE</span>
            <div className="flex overflow-hidden rounded-lg border border-[rgba(255,255,255,0.1)]">
              <button
                onClick={() => setNewCondition("ABOVE")}
                className={`px-4 py-2 text-[10px] font-orbitron font-bold ${
                  newCondition === "ABOVE" ? "bg-[rgba(0,255,102,0.15)] text-[#00FF66]" : "text-[rgba(255,255,255,0.4)]"
                }`}
              >
                ABOVE ↑
              </button>
              <button
                onClick={() => setNewCondition("BELOW")}
                className={`px-4 py-2 text-[10px] font-orbitron font-bold ${
                  newCondition === "BELOW" ? "bg-[rgba(255,0,85,0.15)] text-[#FF0055]" : "text-[rgba(255,255,255,0.4)]"
                }`}
              >
                BELOW ↓
              </button>
            </div>
          </div>
          <div>
            <span className="block font-mono text-[9px] text-[rgba(255,255,255,0.4)] mb-1">TARGET PRICE ($)</span>
            <input
              type="number"
              value={newPrice}
              onChange={(e) => setNewPrice(e.target.value)}
              placeholder={tickers[newSymbol]?.price || "0.00"}
              className="bg-[rgba(0,240,255,0.05)] border border-[rgba(0,240,255,0.3)] text-white font-mono text-sm px-3 py-2 rounded-lg outline-none focus:border-[#00F0FF] w-40"
            />
          </div>
          <button
            onClick={createAlert}
            className="px-6 py-2 bg-[rgba(0,240,255,0.1)] border border-[#00F0FF] text-[#00F0FF] font-orbitron font-bold text-xs rounded-lg hover:bg-[rgba(0,240,255,0.2)] hover:shadow-[0_0_15px_rgba(0,240,255,0.3)] transition-all"
          >
            DEPLOY ALERT
          </button>
        </div>
      </div>

      {/* Active Alerts */}
      <div className="space-y-3 mb-10">
        <h3 className="font-orbitron text-[10px] tracking-widest text-[rgba(255,255,255,0.5)] font-bold">
          DEPLOYED ALERTS ({alerts.filter((a) => !a.triggered).length} ACTIVE)
        </h3>
        <AnimatePresence>
          {alerts.map((alert) => {
            const ticker = tickers[alert.symbol];
            const currentPrice = ticker ? parseFloat(ticker.price) : 0;
            const distance = alert.condition === "ABOVE"
              ? ((alert.price - currentPrice) / currentPrice * 100)
              : ((currentPrice - alert.price) / currentPrice * 100);
            
            return (
              <motion.div
                key={alert.id}
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -50 }}
                className={`border rounded-xl p-4 backdrop-blur-md flex items-center justify-between ${
                  alert.triggered
                    ? "border-[rgba(0,255,102,0.5)] bg-[rgba(0,255,102,0.05)]"
                    : "border-[rgba(0,240,255,0.3)] bg-[rgba(5,15,25,0.4)]"
                }`}
              >
                <div className="flex items-center space-x-4">
                  <div className={`w-3 h-3 rounded-full ${alert.triggered ? "bg-[#00FF66]" : "bg-[#FF5500] animate-pulse"}`} />
                  <div>
                    <span className="font-orbitron text-xs text-white font-bold">{alert.symbol.replace("USDT", "")}</span>
                    <span className={`ml-2 font-mono text-[10px] ${alert.condition === "ABOVE" ? "text-[#00FF66]" : "text-[#FF0055]"}`}>
                      {alert.condition} ${alert.price.toLocaleString()}
                    </span>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  {!alert.triggered && (
                    <span className="font-mono text-[10px] text-[rgba(255,255,255,0.4)]">
                      {distance > 0 ? `${distance.toFixed(2)}% away` : "IMMINENT"}
                    </span>
                  )}
                  {alert.triggered && (
                    <span className="font-mono text-[10px] text-[#00FF66] font-bold">✓ TRIGGERED</span>
                  )}
                  <button
                    onClick={() => deleteAlert(alert.id)}
                    className="text-[rgba(255,255,255,0.3)] hover:text-[#FF0055] transition-colors text-sm"
                  >
                    ✕
                  </button>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
        {alerts.length === 0 && (
          <div className="text-center py-6 text-[rgba(255,255,255,0.2)] font-mono text-xs">
            NO ALERTS DEPLOYED. CREATE ONE ABOVE.
          </div>
        )}
      </div>

      {/* The Wall - Global Events */}
      <div className="space-y-4">
        <h3 className="font-orbitron text-[14px] tracking-widest text-[#00F0FF] font-bold border-b border-[rgba(0,240,255,0.2)] pb-2">
          GLOBAL EVENT RADAR (THE WALL)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <EventFeedColumn />
          <MempoolColumn />
        </div>
      </div>
    </div>
  );
}

function EventFeedColumn() {
  const toasts = useOmniStore((state) => state.toasts);
  const displayToasts = [...toasts].reverse().slice(0, 10);

  return (
    <div className="border border-[rgba(0,240,255,0.1)] rounded-xl bg-[rgba(5,15,25,0.4)] p-4 h-[400px] overflow-y-auto scroll-container">
      <h4 className="font-mono text-[10px] text-[rgba(255,255,255,0.5)] mb-3">LATEST ANOMALIES</h4>
      <div className="space-y-2">
        <AnimatePresence>
          {displayToasts.map((toast) => {
            const isWhale = toast.type === "whale";
            const isRekt = toast.type === "rekt";
            return (
              <motion.div
                key={toast.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className={`p-3 rounded-lg border ${
                  isWhale ? "border-[rgba(0,240,255,0.3)] bg-[rgba(0,240,255,0.05)] text-[#00F0FF]"
                  : isRekt ? "border-[rgba(255,0,85,0.4)] bg-[rgba(255,0,85,0.1)] text-[#FF0055]"
                  : "border-[rgba(255,255,255,0.1)] text-white"
                }`}
              >
                <div className="font-orbitron text-[10px] font-bold mb-1">{toast.title}</div>
                <div className="font-mono text-[10px] opacity-80">{toast.message}</div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}

function MempoolColumn() {
  const mempoolEvents = useOmniStore((state) => state.mempoolEvents);
  const events = mempoolEvents.slice(0, 10);

  return (
    <div className="border border-[rgba(139,0,255,0.2)] rounded-xl bg-[rgba(5,15,25,0.4)] p-4 h-[400px] overflow-y-auto scroll-container">
      <h4 className="font-mono text-[10px] text-[rgba(139,0,255,0.8)] mb-3">ON-CHAIN MEMPOOL</h4>
      <div className="space-y-2">
        <AnimatePresence>
          {events.map((ev, i) => (
            <motion.div
              key={ev.hash + i}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="p-3 rounded-lg border border-[rgba(139,0,255,0.3)] bg-[rgba(139,0,255,0.05)] text-[#8B00FF]"
            >
              <div className="flex justify-between font-mono text-[10px]">
                <span className="font-bold">{ev.network}</span>
                <span>{ev.value}</span>
              </div>
              <div className="font-mono text-[8px] opacity-60 mt-1 truncate">Tx: {ev.hash}</div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
