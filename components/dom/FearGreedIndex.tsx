"use client";

import React, { useEffect, useState } from "react";

interface FNGData {
  value: string;
  value_classification: string;
}

export default function FearGreedIndex() {
  const [fng, setFng] = useState<FNGData | null>(null);

  useEffect(() => {
    let isMounted = true;
    const fetchFNG = async () => {
      try {
        const res = await fetch("https://api.alternative.me/fng/?limit=1");
        const json = await res.json();
        if (isMounted && json && json.data && json.data.length > 0) {
          setFng(json.data[0]);
        }
      } catch (err) {
        console.error("Failed to fetch Fear & Greed Index", err);
      }
    };

    fetchFNG();
    // Update every hour
    const interval = setInterval(fetchFNG, 3600000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  if (!fng) return null;

  const value = parseInt(fng.value);
  let colorClass = "text-[#00F0FF]"; // Default Cyan
  let barColor = "bg-[#00F0FF]";
  let shadow = "shadow-[0_0_10px_#00F0FF]";

  if (value < 25) {
    colorClass = "text-[#FF0055]"; // Extreme Fear (Red)
    barColor = "bg-[#FF0055]";
    shadow = "shadow-[0_0_10px_#FF0055]";
  } else if (value < 45) {
    colorClass = "text-[#FF5500]"; // Fear (Orange)
    barColor = "bg-[#FF5500]";
    shadow = "shadow-[0_0_10px_#FF5500]";
  } else if (value > 75) {
    colorClass = "text-[#00FF66]"; // Extreme Greed (Green)
    barColor = "bg-[#00FF66]";
    shadow = "shadow-[0_0_10px_#00FF66]";
  } else if (value > 55) {
    colorClass = "text-[#00F0FF]"; // Greed (Cyan)
  }

  return (
    <div className="glass-panel p-3 rounded-lg flex items-center justify-between w-[220px]">
      <div className="flex flex-col">
        <span className="font-mono text-[9px] text-[rgba(255,255,255,0.4)]">SENTIMENT INDEX</span>
        <span className={`font-orbitron font-bold text-sm tracking-wide ${colorClass}`}>
          {fng.value_classification.toUpperCase()}
        </span>
      </div>
      <div className="relative w-10 h-10 flex items-center justify-center">
        <svg className="absolute inset-0 w-full h-full transform -rotate-90">
          <circle 
            cx="20" cy="20" r="16" 
            fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="3" 
          />
          <circle 
            cx="20" cy="20" r="16" 
            fill="none" stroke="currentColor" strokeWidth="3" 
            strokeDasharray="100" 
            strokeDashoffset={100 - value} 
            className={`${colorClass} transition-all duration-1000 ease-out`}
          />
        </svg>
        <span className="font-mono text-[10px] font-bold text-white z-10">{value}</span>
      </div>
    </div>
  );
}
