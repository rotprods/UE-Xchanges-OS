"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { useOmniStore } from "../../store/omniStore";

const routeTitles: Record<string, string> = {
  "/": "COMMAND CENTER",
  "/charts": "ADVANCED CHARTS",
  "/trading": "TRADING TERMINAL",
  "/intelligence": "MARKET INTELLIGENCE",
  "/alerts": "ALERT COMMANDER",
  "/settings": "SYSTEM CONFIG",
};

export default function TopBar() {
  const pathname = usePathname();
  const marketMode = useOmniStore((state) => state.marketMode);
  const setMarketMode = useOmniStore((state) => state.setMarketMode);
  const audioEnabled = useOmniStore((state) => state.audioEnabled);
  const toggleAudio = useOmniStore((state) => state.toggleAudio);
  const stats = useOmniStore((state) => state.stats);

  const title = routeTitles[pathname] || "CHRONOS QUANTUM";

  return (
    <header className="h-14 bg-[rgba(5,5,15,0.9)] backdrop-blur-xl border-b border-[rgba(0,240,255,0.1)] flex items-center justify-between px-6 ml-16 sticky top-0 z-40">
      {/* Left: Screen Title */}
      <div className="flex items-center space-x-4">
        <h1 className="font-orbitron text-sm tracking-widest text-white font-bold">{title}</h1>
        <div className="hidden sm:flex items-center space-x-2">
          <div className="w-1.5 h-1.5 rounded-full bg-[#00FF66] animate-pulse shadow-[0_0_6px_#00FF66]" />
          <span className="font-mono text-[9px] text-[rgba(255,255,255,0.4)]">
            {stats.txsPerSecond} TX/s
          </span>
        </div>
      </div>

      {/* Right: Controls */}
      <div className="flex items-center space-x-4">
        {/* Market Mode Toggle */}
        <div className="flex items-center bg-[rgba(0,0,0,0.4)] rounded-lg border border-[rgba(255,255,255,0.1)] overflow-hidden">
          <button
            onClick={() => setMarketMode("CRYPTO")}
            className={`px-3 py-1.5 text-[9px] font-orbitron font-bold tracking-wider transition-all ${
              marketMode === "CRYPTO"
                ? "bg-[rgba(0,240,255,0.15)] text-[#00F0FF] shadow-[inset_0_0_10px_rgba(0,240,255,0.1)]"
                : "text-[rgba(255,255,255,0.4)] hover:text-white"
            }`}
          >
            CRYPTO
          </button>
          <button
            onClick={() => setMarketMode("STOCKS")}
            className={`px-3 py-1.5 text-[9px] font-orbitron font-bold tracking-wider transition-all ${
              marketMode === "STOCKS"
                ? "bg-[rgba(139,0,255,0.15)] text-[#8B00FF] shadow-[inset_0_0_10px_rgba(139,0,255,0.1)]"
                : "text-[rgba(255,255,255,0.4)] hover:text-white"
            }`}
          >
            STOCKS
          </button>
        </div>

        {/* Audio Toggle */}
        <button
          onClick={toggleAudio}
          className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all text-sm ${
            audioEnabled
              ? "bg-[rgba(0,240,255,0.1)] border border-[rgba(0,240,255,0.3)] shadow-[0_0_8px_rgba(0,240,255,0.2)]"
              : "bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)]"
          }`}
        >
          {audioEnabled ? "🔊" : "🔇"}
        </button>

        {/* Clock */}
        <div className="hidden md:block font-mono text-[10px] text-[rgba(255,255,255,0.5)]">
          <Clock />
        </div>
      </div>
    </header>
  );
}

function Clock() {
  const [time, setTime] = React.useState("");

  React.useEffect(() => {
    const update = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString("en-US", { hour12: false, timeZone: "UTC" }));
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  return <span>{time} UTC</span>;
}
