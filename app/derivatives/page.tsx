"use client";

import React, { useState, useMemo, useEffect } from 'react';
import dynamic from 'next/dynamic';

// Dynamically import the canvas to avoid SSR issues with Three.js
const VolSurfaceCanvas = dynamic(
  () => import('@/components/canvas/VolSurfaceCanvas'),
  { ssr: false }
);

const EXPIRIES = ['1W', '1M', '3M'];
const STRIKES = [50000, 60000, 70000, 80000, 90000, 100000];

type OptionData = {
  bid: number;
  ask: number;
  iv: number;
  delta: number;
  gamma: number;
};

type OptionRow = {
  strike: number;
  call: OptionData;
  put: OptionData;
};

function generateMockChain(expiry: string): OptionRow[] {
  // Use expiry to slightly tweak the mock data
  const expiryMultiplier = expiry === '1W' ? 1 : expiry === '1M' ? 1.5 : 2;

  return STRIKES.map((strike) => {
    // arbitrary pseudo-random looking logic based on strike
    const normalizedStrike = strike / 100000;
    
    return {
      strike,
      call: {
        bid: +(1500 * normalizedStrike * expiryMultiplier).toFixed(1),
        ask: +(1550 * normalizedStrike * expiryMultiplier).toFixed(1),
        iv: +(45 + (1 - normalizedStrike) * 20 * expiryMultiplier).toFixed(1),
        delta: +(0.8 - normalizedStrike * 0.5).toFixed(2),
        gamma: +(0.02 * expiryMultiplier).toFixed(3),
      },
      put: {
        bid: +(1200 * (1 - normalizedStrike) * expiryMultiplier).toFixed(1),
        ask: +(1250 * (1 - normalizedStrike) * expiryMultiplier).toFixed(1),
        iv: +(45 + normalizedStrike * 20 * expiryMultiplier).toFixed(1),
        delta: +(-0.2 - normalizedStrike * 0.5).toFixed(2),
        gamma: +(0.02 * expiryMultiplier).toFixed(3),
      }
    };
  });
}

export default function DerivativesPage() {
  const [selectedExpiry, setSelectedExpiry] = useState(EXPIRIES[0]);
  const [chainData, setChainData] = useState<OptionRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    
    const fetchDeribit = async () => {
      try {
        setLoading(true);
        const res = await fetch("/api/deribit");
        const json = await res.json();
        const results = json?.result || [];
        
        // Group by strike for a mock-like structure but real data
        const strikesMap: Record<number, any> = {};
        
        results.forEach((item: any) => {
          // item.instrument_name e.g. "BTC-27DEC24-100000-C"
          const parts = item.instrument_name.split("-");
          if (parts.length !== 4) return;
          const strike = parseInt(parts[2], 10);
          const type = parts[3]; // 'C' or 'P'
          
          if (!strikesMap[strike]) {
            strikesMap[strike] = { strike, call: null, put: null };
          }
          
          const optData = {
            bid: item.bid_price || 0,
            ask: item.ask_price || 0,
            iv: item.mark_iv || 0,
            delta: 0, // Simplified for now since book_summary doesn't have greeks
            gamma: 0,
          };
          
          if (type === "C") strikesMap[strike].call = optData;
          if (type === "P") strikesMap[strike].put = optData;
        });

        // Filter valid strikes with both calls and puts and sort them
        const validRows = Object.values(strikesMap)
          .filter(row => row.call && row.put)
          .sort((a, b) => a.strike - b.strike)
          .slice(0, 10); // Take top 10 for UI performance

        if (isMounted) {
          setChainData(validRows);
          setLoading(false);
        }
      } catch (err) {
        console.error("Deribit Fetch Error:", err);
        if (isMounted) setLoading(false);
      }
    };

    fetchDeribit();
    const intervalId = setInterval(fetchDeribit, 5000);

    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, [selectedExpiry]);

  return (
    <div className="min-h-screen bg-[#05050A] text-white p-8 font-mono">
      <div className="max-w-7xl mx-auto space-y-8">
        
        <header className="flex flex-col md:flex-row md:items-end justify-between border-b border-[rgba(0,240,255,0.2)] pb-4">
          <div>
            <h1 className="text-4xl font-bold tracking-tighter" style={{ textShadow: '0 0 10px #00F0FF' }}>
              DERIVATIVES &amp; OPTIONS MATRIX
            </h1>
            <p className="text-[#00F0FF] opacity-70 mt-2">BTC/USD OPTION CHAIN &amp; VOLATILITY SURFACE</p>
          </div>
          
          <div className="flex gap-2 mt-4 md:mt-0">
            {EXPIRIES.map(exp => (
              <button
                key={exp}
                onClick={() => setSelectedExpiry(exp)}
                className={`px-4 py-2 border transition-all duration-300 ${
                  selectedExpiry === exp 
                    ? 'border-[#00F0FF] bg-[rgba(0,240,255,0.1)] text-[#00F0FF] shadow-[0_0_10px_rgba(0,240,255,0.5)]' 
                    : 'border-[rgba(255,255,255,0.1)] hover:border-[rgba(0,240,255,0.5)] text-gray-400'
                }`}
              >
                {exp}
              </button>
            ))}
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Volatility Surface Canvas Panel */}
          <div className="lg:col-span-3 rounded-xl border border-[rgba(0,240,255,0.1)] bg-[rgba(10,10,20,0.6)] backdrop-blur-md overflow-hidden relative" style={{ height: '500px' }}>
            <div className="absolute top-4 left-4 z-10 pointer-events-none">
              <h2 className="text-[#E024FF] font-semibold tracking-wider text-sm shadow-sm" style={{ textShadow: '0 0 5px #E024FF' }}>
                IMPLIED VOLATILITY SURFACE
              </h2>
            </div>
            <VolSurfaceCanvas />
          </div>

          {/* Options Chain Data Table */}
          <div className="lg:col-span-3 rounded-xl border border-[rgba(0,240,255,0.1)] bg-[rgba(10,10,20,0.6)] backdrop-blur-md overflow-x-auto">
             <table className="w-full text-sm text-left whitespace-nowrap">
               <thead className="bg-[rgba(0,0,0,0.4)] text-xs uppercase border-b border-[rgba(0,240,255,0.1)]">
                 <tr>
                   <th colSpan={5} className="px-6 py-4 text-center border-r border-[rgba(0,240,255,0.1)] text-[#00FF66]" style={{ textShadow: '0 0 5px #00FF66' }}>CALLS</th>
                   <th className="px-6 py-4 text-center text-white bg-[rgba(255,255,255,0.05)] border-r border-[rgba(0,240,255,0.1)]">STRIKE</th>
                   <th colSpan={5} className="px-6 py-4 text-center text-[#FF0055]" style={{ textShadow: '0 0 5px #FF0055' }}>PUTS</th>
                 </tr>
                 <tr className="border-b border-[rgba(0,240,255,0.1)] text-gray-400">
                   {/* Calls */}
                   <th className="px-4 py-2 border-r border-[rgba(0,240,255,0.1)] border-t border-[rgba(0,240,255,0.1)]">BID</th>
                   <th className="px-4 py-2 border-r border-[rgba(0,240,255,0.1)] border-t border-[rgba(0,240,255,0.1)]">ASK</th>
                   <th className="px-4 py-2 border-r border-[rgba(0,240,255,0.1)] border-t border-[rgba(0,240,255,0.1)]">IV %</th>
                   <th className="px-4 py-2 border-r border-[rgba(0,240,255,0.1)] border-t border-[rgba(0,240,255,0.1)]">DELTA</th>
                   <th className="px-4 py-2 border-r border-[rgba(0,240,255,0.1)] border-t border-[rgba(0,240,255,0.1)]">GAMMA</th>
                   
                   {/* Strike */}
                   <th className="px-4 py-2 text-center bg-[rgba(255,255,255,0.05)] border-r border-[rgba(0,240,255,0.1)] border-t border-[rgba(0,240,255,0.1)]">PRICE</th>
                   
                   {/* Puts */}
                   <th className="px-4 py-2 border-r border-[rgba(0,240,255,0.1)] border-t border-[rgba(0,240,255,0.1)]">BID</th>
                   <th className="px-4 py-2 border-r border-[rgba(0,240,255,0.1)] border-t border-[rgba(0,240,255,0.1)]">ASK</th>
                   <th className="px-4 py-2 border-r border-[rgba(0,240,255,0.1)] border-t border-[rgba(0,240,255,0.1)]">IV %</th>
                   <th className="px-4 py-2 border-r border-[rgba(0,240,255,0.1)] border-t border-[rgba(0,240,255,0.1)]">DELTA</th>
                   <th className="px-4 py-2 border-t border-[rgba(0,240,255,0.1)] border-t border-[rgba(0,240,255,0.1)]">GAMMA</th>
                 </tr>
               </thead>
               <tbody>
                 {chainData.map((row) => (
                   <tr key={row.strike} className="border-b border-[rgba(0,240,255,0.05)] hover:bg-[rgba(0,240,255,0.05)] transition-colors">
                     {/* Calls */}
                     <td className="px-4 py-3 text-[#00FF66] border-r border-[rgba(0,240,255,0.1)]">{row.call.bid}</td>
                     <td className="px-4 py-3 text-[#00FF66] border-r border-[rgba(0,240,255,0.1)]">{row.call.ask}</td>
                     <td className="px-4 py-3 text-[#8B00FF] border-r border-[rgba(0,240,255,0.1)]">{row.call.iv}</td>
                     <td className="px-4 py-3 text-gray-300 border-r border-[rgba(0,240,255,0.1)]">{row.call.delta}</td>
                     <td className="px-4 py-3 text-gray-300 border-r border-[rgba(0,240,255,0.1)]">{row.call.gamma}</td>
                     
                     {/* Strike */}
                     <td className="px-4 py-3 font-bold text-center bg-[rgba(255,255,255,0.05)] text-[#00F0FF] border-r border-[rgba(0,240,255,0.1)] text-lg">
                       ${row.strike.toLocaleString()}
                     </td>
                     
                     {/* Puts */}
                     <td className="px-4 py-3 text-[#FF0055] border-r border-[rgba(0,240,255,0.1)]">{row.put.bid}</td>
                     <td className="px-4 py-3 text-[#FF0055] border-r border-[rgba(0,240,255,0.1)]">{row.put.ask}</td>
                     <td className="px-4 py-3 text-[#8B00FF] border-r border-[rgba(0,240,255,0.1)]">{row.put.iv}</td>
                     <td className="px-4 py-3 text-gray-300 border-r border-[rgba(0,240,255,0.1)]">{row.put.delta}</td>
                     <td className="px-4 py-3 text-gray-300">{row.put.gamma}</td>
                   </tr>
                 ))}
               </tbody>
             </table>
          </div>
        </div>
      </div>
    </div>
  );
}
