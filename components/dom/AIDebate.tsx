"use client";

import React, { useEffect, useState, useRef } from "react";
import { useOmniStore } from "@/store/omniStore";

// Personas
const PERSONAS = {
  ALPHA_QUANT: {
    name: "ALPHA_QUANT",
    color: "#00F0FF",
  },
  DEGEN_BOT: {
    name: "DEGEN_BOT",
    color: "#FF5500",
  },
};

interface Message {
  id: string;
  sender: string;
  text: string;
  color: string;
  timestamp: number;
}

export default function AIDebate({ fearGreed = 50 }: { fearGreed?: number }) {
  const latestCandle = useOmniStore((state) => state.latestCandle);
  const tickers = useOmniStore((state) => state.tickers);
  
  const [messages, setMessages] = useState<Message[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto scroll
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    const generateMessage = () => {
      // Find a popular ticker or default to 50000
      const btcPrice = tickers["BTC"]?.price || latestCandle?.close || 50000;
      
      const isAlpha = Math.random() > 0.5;
      const persona = isAlpha ? PERSONAS.ALPHA_QUANT : PERSONAS.DEGEN_BOT;
      
      let text = "";
      if (isAlpha) {
        if (fearGreed > 75) {
          text = `Market exuberance detected (F&G: ${fearGreed}). Scaling out of long positions on BTC at $${btcPrice.toLocaleString(undefined, { maximumFractionDigits: 2 })}. Volatility expansion probable.`;
        } else if (fearGreed < 25) {
          text = `Statistical deviation extreme. Deploying mean-reversion algo. Accumulating delta-neutral positions at $${btcPrice.toLocaleString(undefined, { maximumFractionDigits: 2 })}.`;
        } else {
          text = `Price action on BTC converging around $${btcPrice.toLocaleString(undefined, { maximumFractionDigits: 2 })}. Re-balancing portfolio beta.`;
        }
      } else {
        if (fearGreed > 75) {
          text = `LFG!!! BTC at $${btcPrice.toLocaleString(undefined, { maximumFractionDigits: 2 })} is just the start! We are going straight to Valhalla! 🚀🌕 HODL!`;
        } else if (fearGreed < 25) {
          text = `Buy the dip you cowards! Liquidation hunting in progress. Diamond hands! 💎🙌`;
        } else {
          text = `Sideways chop is boring. Awaiting the next pump. NGMI if you sell now.`;
        }
      }

      setMessages((prev) => {
        const newMsg: Message = {
          id: Date.now().toString() + Math.random().toString(),
          sender: persona.name,
          text,
          color: persona.color,
          timestamp: Date.now(),
        };
        const next = [...prev, newMsg];
        if (next.length > 50) return next.slice(next.length - 50);
        return next;
      });
    };

    // First message immediately
    const timeout = setTimeout(generateMessage, 1000);

    // Then every 5-10s
    const interval = setInterval(() => {
      generateMessage();
    }, 5000 + Math.random() * 5000);

    return () => {
      clearTimeout(timeout);
      clearInterval(interval);
    };
  }, [tickers, latestCandle, fearGreed]);

  return (
    <div className="w-full h-64 flex flex-col bg-[rgba(10,10,20,0.6)] backdrop-blur-md rounded-xl border border-[rgba(0,240,255,0.1)] p-4 overflow-hidden relative">
      <div className="text-[#00F0FF] text-sm uppercase font-bold mb-4 tracking-wider flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-[#00F0FF] animate-pulse" />
        AI Sentiment Synthesis
      </div>
      
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto pr-2 space-y-4 scrollbar-thin scrollbar-thumb-[rgba(0,240,255,0.2)] pb-2"
      >
        {messages.length === 0 ? (
          <div className="text-white/30 text-xs font-mono italic">Initializing neural debate...</div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className="flex flex-col gap-1 text-[11px] font-mono">
              <div className="flex justify-between items-baseline">
                <span className="font-bold tracking-wider" style={{ color: msg.color }}>
                  [{msg.sender}]
                </span>
                <span className="text-[9px] text-white/30">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <div className="text-white/80 leading-relaxed pl-2 border-l border-opacity-30" style={{ borderLeftColor: msg.color }}>
                {msg.text}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
