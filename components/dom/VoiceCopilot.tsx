"use client";

import React, { useState, useEffect, useRef } from "react";
import { useOmniStore } from "@/store/omniStore";
import { motion } from "framer-motion";

export const VoiceCopilot = () => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const recognitionRef = useRef<any>(null);
  
  const { portfolio, executeTrade, toggleAutoTrade, autoTradeEnabled, tickers } = useOmniStore();

  useEffect(() => {
    if (typeof window !== "undefined") {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        recognitionRef.current = new SpeechRecognition();
        recognitionRef.current.continuous = false;
        recognitionRef.current.interimResults = false;
        recognitionRef.current.lang = "en-US";

        recognitionRef.current.onresult = (event: any) => {
          const current = event.resultIndex;
          const transcriptText = event.results[current][0].transcript;
          setTranscript(transcriptText);
          handleCommand(transcriptText.toLowerCase());
        };

        recognitionRef.current.onerror = (event: any) => {
          console.error("Speech recognition error", event.error);
          setIsListening(false);
        };

        recognitionRef.current.onend = () => {
          setIsListening(false);
        };
      }
    }
  }, [portfolio, autoTradeEnabled, tickers]);

  const speak = (text: string) => {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      // Cancel any ongoing speech
      window.speechSynthesis.cancel();
      const msg = new SpeechSynthesisUtterance(text);
      msg.pitch = 0.4;
      msg.rate = 1.2;
      
      const voices = window.speechSynthesis.getVoices();
      // Try to find a specific robotic voice, or fallback to default
      const roboVoice = voices.find(v => v.name.includes("Google UK English Male") || v.name.includes("Samantha"));
      if (roboVoice) {
        msg.voice = roboVoice;
      }
      
      window.speechSynthesis.speak(msg);
    }
  };

  const getSymbolFromAsset = (asset: string) => {
    if (asset.includes("bitcoin") || asset.includes("btc")) return "BTCUSDT";
    if (asset.includes("ethereum") || asset.includes("eth")) return "ETHUSDT";
    if (asset.includes("solana") || asset.includes("sol")) return "SOLUSDT";
    return null;
  };

  const getAssetNameFromSymbol = (symbol: string) => {
    if (symbol === "BTCUSDT") return "Bitcoin";
    if (symbol === "ETHUSDT") return "Ethereum";
    if (symbol === "SOLUSDT") return "Solana";
    return symbol;
  };

  const handleCommand = (cmd: string) => {
    if (cmd.includes("skynet on")) {
      if (!autoTradeEnabled) toggleAutoTrade();
      speak("Skynet auto-trading activated. Assuming control.");
      return;
    }
    
    if (cmd.includes("skynet off")) {
      if (autoTradeEnabled) toggleAutoTrade();
      speak("Skynet deactivated. Manual control restored.");
      return;
    }

    if (cmd.includes("status")) {
      const usdt = portfolio.usdt.toFixed(2);
      const btc = (portfolio.assets["BTCUSDT"] || 0).toFixed(4);
      const eth = (portfolio.assets["ETHUSDT"] || 0).toFixed(4);
      speak(`Portfolio status. You have ${usdt} USDT. ${btc} Bitcoin. ${eth} Ethereum.`);
      return;
    }

    // Buy [amount] [asset]
    const buyMatch = cmd.match(/buy\s+(\d+)\s+(\w+)/);
    if (buyMatch) {
      const amountStr = buyMatch[1];
      const asset = buyMatch[2];
      const symbol = getSymbolFromAsset(asset);
      const amountUsd = parseFloat(amountStr);
      
      if (symbol) {
        const priceStr = tickers[symbol]?.price;
        if (priceStr) {
          executeTrade(symbol, "BUY", amountUsd, parseFloat(priceStr));
          speak(`Executed buy of ${amountUsd} dollars of ${asset}.`);
        } else {
          speak(`Price data unavailable for ${asset}.`);
        }
      } else {
        speak(`Asset ${asset} not recognized.`);
      }
      return;
    }

    // Sell all [asset]
    const sellAllMatch = cmd.match(/sell\s+all\s+(\w+)/);
    if (sellAllMatch) {
      const asset = sellAllMatch[1];
      const symbol = getSymbolFromAsset(asset);
      
      if (symbol) {
        const balanceTokens = portfolio.assets[symbol] || 0;
        if (balanceTokens > 0) {
          const priceStr = tickers[symbol]?.price;
          if (priceStr) {
            const price = parseFloat(priceStr);
            const amountUsd = balanceTokens * price;
            executeTrade(symbol, "SELL", amountUsd, price);
            speak(`Executed sell of all ${asset} balance.`);
          } else {
            speak(`Price data unavailable for ${asset}.`);
          }
        } else {
          speak(`You have no ${asset} to sell.`);
        }
      } else {
        speak(`Asset ${asset} not recognized.`);
      }
      return;
    }

    speak("Command not recognized. Please try again.");
  };

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    } else {
      setTranscript("");
      recognitionRef.current?.start();
      setIsListening(true);
    }
  };

  if (typeof window === "undefined") return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex items-center gap-4">
      {transcript && (
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 20 }}
          className="px-4 py-2 bg-[rgba(10,10,20,0.8)] backdrop-blur-md border border-[#00F0FF]/30 rounded-xl text-[#00F0FF] text-sm font-mono shadow-[0_0_15px_rgba(0,240,255,0.2)] max-w-xs truncate"
        >
          {transcript}
        </motion.div>
      )}

      <button
        onClick={toggleListening}
        className={`relative w-14 h-14 flex items-center justify-center rounded-full transition-all duration-300 ${
          isListening 
            ? "bg-[#FF0055]/20 border-2 border-[#FF0055] shadow-[0_0_30px_rgba(255,0,85,0.6)]" 
            : "bg-[#00F0FF]/10 border border-[#00F0FF]/50 hover:bg-[#00F0FF]/20 hover:shadow-[0_0_20px_rgba(0,240,255,0.4)]"
        }`}
      >
        {isListening && (
          <>
            <span className="absolute inset-0 rounded-full border border-[#FF0055] animate-ping opacity-75" />
            <span className="absolute -inset-2 rounded-full border border-[#FF0055]/30 animate-pulse" />
          </>
        )}
        
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke={isListening ? "#FF0055" : "#00F0FF"} 
          strokeWidth="2" 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          className="w-6 h-6"
        >
          <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
          <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
          <line x1="12" x2="12" y1="19" y2="22" />
        </svg>
      </button>
    </div>
  );
};
