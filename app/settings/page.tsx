"use client";

import React from "react";
import { useOmniStore } from "../../store/omniStore";
import ApiConfigPanel from "../../components/dom/ApiConfigPanel";

export default function SettingsPage() {
  const audioEnabled = useOmniStore((state) => state.audioEnabled);
  const toggleAudio = useOmniStore((state) => state.toggleAudio);
  const marketMode = useOmniStore((state) => state.marketMode);
  const setMarketMode = useOmniStore((state) => state.setMarketMode);
  const portfolio = useOmniStore((state) => state.portfolio);

  const resetPortfolio = () => {
    // Reset via direct store mutation
    useOmniStore.setState({
      portfolio: { usdt: 1000000, assets: {}, avgCost: {} },
    });
  };

  return (
    <div className="p-6 space-y-8 max-w-2xl mx-auto">
      <div>
        <h2 className="font-orbitron text-xl text-[#00F0FF] font-bold tracking-wider">SYSTEM CONFIG</h2>
        <p className="font-mono text-[10px] text-[rgba(255,255,255,0.4)] mt-1">Terminal preferences and system configuration</p>
      </div>

      {/* Audio */}
      <div className="border border-[rgba(0,240,255,0.3)] bg-[rgba(5,15,25,0.4)] backdrop-blur-md rounded-2xl p-6 space-y-4">
        <h3 className="font-orbitron text-[10px] tracking-widest text-[#00F0FF] font-bold">AUDIO ENGINE</h3>
        <div className="flex justify-between items-center">
          <div>
            <p className="font-mono text-xs text-white">Sonification System</p>
            <p className="font-mono text-[9px] text-[rgba(255,255,255,0.4)]">Enable audio feedback for trades, whales, and liquidations</p>
          </div>
          <button
            onClick={toggleAudio}
            className={`w-14 h-7 rounded-full transition-all relative ${
              audioEnabled ? "bg-[#00F0FF] shadow-[0_0_15px_rgba(0,240,255,0.5)]" : "bg-[rgba(255,255,255,0.1)]"
            }`}
          >
            <div
              className={`absolute top-1 w-5 h-5 rounded-full bg-white transition-all shadow-md ${
                audioEnabled ? "left-8" : "left-1"
              }`}
            />
          </button>
        </div>
      </div>

      {/* Market Mode */}
      <div className="border border-[rgba(139,0,255,0.3)] bg-[rgba(5,15,25,0.4)] backdrop-blur-md rounded-2xl p-6 space-y-4">
        <h3 className="font-orbitron text-[10px] tracking-widest text-[#8B00FF] font-bold">DEFAULT MARKET</h3>
        <div className="flex space-x-4">
          <button
            onClick={() => setMarketMode("CRYPTO")}
            className={`flex-1 py-3 rounded-lg font-orbitron text-xs font-bold border transition-all ${
              marketMode === "CRYPTO"
                ? "border-[#00F0FF] bg-[rgba(0,240,255,0.1)] text-[#00F0FF] shadow-[0_0_10px_rgba(0,240,255,0.2)]"
                : "border-[rgba(255,255,255,0.1)] text-[rgba(255,255,255,0.4)]"
            }`}
          >
            CRYPTO
          </button>
          <button
            onClick={() => setMarketMode("STOCKS")}
            className={`flex-1 py-3 rounded-lg font-orbitron text-xs font-bold border transition-all ${
              marketMode === "STOCKS"
                ? "border-[#8B00FF] bg-[rgba(139,0,255,0.1)] text-[#8B00FF] shadow-[0_0_10px_rgba(139,0,255,0.2)]"
                : "border-[rgba(255,255,255,0.1)] text-[rgba(255,255,255,0.4)]"
            }`}
          >
            STOCKS
          </button>
        </div>
      </div>

      {/* Real Execution API Config */}
      <ApiConfigPanel />

      {/* Portfolio Reset */}
      <div className="border border-[rgba(255,0,85,0.3)] bg-[rgba(5,15,25,0.4)] backdrop-blur-md rounded-2xl p-6 space-y-4">
        <h3 className="font-orbitron text-[10px] tracking-widest text-[#FF0055] font-bold">DANGER ZONE</h3>
        <div className="flex justify-between items-center">
          <div>
            <p className="font-mono text-xs text-white">Reset Paper Trading Portfolio</p>
            <p className="font-mono text-[9px] text-[rgba(255,255,255,0.4)]">
              Current balance: ${portfolio.usdt.toLocaleString(undefined, { maximumFractionDigits: 0 })} USDT + {Object.keys(portfolio.assets).length} positions
            </p>
          </div>
          <button
            onClick={resetPortfolio}
            className="px-4 py-2 border border-[#FF0055] text-[#FF0055] font-orbitron text-[10px] font-bold rounded-lg hover:bg-[rgba(255,0,85,0.1)] transition-all"
          >
            RESET TO $1M
          </button>
        </div>
      </div>

      {/* System Info */}
      <div className="border border-[rgba(255,255,255,0.1)] bg-[rgba(5,15,25,0.4)] backdrop-blur-md rounded-2xl p-6 space-y-3">
        <h3 className="font-orbitron text-[10px] tracking-widest text-[rgba(255,255,255,0.5)] font-bold">SYSTEM INFO</h3>
        <div className="space-y-2 font-mono text-[10px]">
          <div className="flex justify-between">
            <span className="text-[rgba(255,255,255,0.4)]">Version</span>
            <span className="text-white">Chronos Quantum v3.0.0</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[rgba(255,255,255,0.4)]">Engine</span>
            <span className="text-white">Next.js 16 + Turbopack</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[rgba(255,255,255,0.4)]">Renderer</span>
            <span className="text-white">Three.js R184 (WebGL2)</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[rgba(255,255,255,0.4)]">Data Sources</span>
            <span className="text-white">Binance WS + CoinGecko + Mempool.space</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[rgba(255,255,255,0.4)]">Network Protocol</span>
            <span className="text-white">PeerJS (WebRTC P2P)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
