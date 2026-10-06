"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useOmniStore } from "../../store/omniStore";

export default function AiCopilot() {
  const [isOpen, setIsOpen] = useState(false);
  const [text, setText] = useState("Awaiting voice protocol...");
  const [isTyping, setIsTyping] = useState(false);
  const [isListening, setIsListening] = useState(false);
  
  const marketMode = useOmniStore(state => state.marketMode);
  const setMarketMode = useOmniStore(state => state.setMarketMode);
  const setChartSymbol = useOmniStore(state => state.setChartSymbol);
  const audioEnabled = useOmniStore(state => state.audioEnabled);
  
  const recognitionRef = useRef<any>(null);

  // Initialize Speech Recognition
  useEffect(() => {
    if (typeof window !== "undefined") {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        recognitionRef.current = new SpeechRecognition();
        recognitionRef.current.continuous = false;
        recognitionRef.current.lang = "en-US";
        
        recognitionRef.current.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript.toLowerCase();
          handleVoiceCommand(transcript);
        };
        
        recognitionRef.current.onend = () => {
          setIsListening(false);
        };
      }
    }
  }, []);

  const speak = (msg: string) => {
    if (!audioEnabled || !window.speechSynthesis) return;
    const utterance = new SpeechSynthesisUtterance(msg);
    utterance.pitch = 0.8;
    utterance.rate = 1.1;
    // Try to find a robotic/english voice
    const voices = window.speechSynthesis.getVoices();
    const roboticVoice = voices.find(v => v.name.includes("Google") || v.name.includes("Zira")) || voices[0];
    if (roboticVoice) utterance.voice = roboticVoice;
    
    window.speechSynthesis.speak(utterance);
  };

  const simulateTyping = async (targetText: string) => {
    setIsTyping(true);
    setText("");
    speak(targetText);
    
    for (let i = 0; i <= targetText.length; i++) {
      setText(targetText.slice(0, i));
      await new Promise(r => setTimeout(r, 20 + Math.random() * 20));
    }
    setIsTyping(false);
  };

  const handleVoiceCommand = (cmd: string) => {
    console.log("Voice Command Received:", cmd);
    if (cmd.includes("nvidia") || cmd.includes("stocks") || cmd.includes("equities")) {
      setMarketMode("STOCKS");
      setChartSymbol("NVDA");
      simulateTyping("Switching to Equities Matrix. Targeting NVIDIA.");
    } else if (cmd.includes("bitcoin") || cmd.includes("crypto")) {
      setMarketMode("CRYPTO");
      setChartSymbol("BTCUSDT");
      simulateTyping("Switching to Crypto Matrix. Targeting Bitcoin.");
    } else if (cmd.includes("status") || cmd.includes("report")) {
      const isCrypto = marketMode === "CRYPTO";
      const msg = isCrypto ? "Crypto markets are highly volatile. Recommend caution on leverage." : "Equities show steady algorithmic accumulation.";
      simulateTyping(msg);
    } else {
      simulateTyping("Command not recognized. Please specify target asset.");
    }
  };

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current?.start();
        setIsListening(true);
        setText("Listening...");
      } catch (e) {
        console.error(e);
      }
    }
  };

  return (
    <>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 w-12 h-12 rounded-full bg-[rgba(0,240,255,0.1)] border border-[#00F0FF] shadow-[0_0_15px_rgba(0,240,255,0.3)] flex items-center justify-center hover:scale-110 transition-transform backdrop-blur-md"
      >
        <span className="relative flex h-3 w-3">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00F0FF] opacity-75"></span>
          <span className="relative inline-flex rounded-full h-3 w-3 bg-[#00F0FF]"></span>
        </span>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 50, scale: 0.9 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            className="fixed bottom-24 right-6 z-50 w-80 glass-panel border border-[rgba(0,240,255,0.3)] rounded-xl overflow-hidden shadow-[0_0_30px_rgba(0,0,0,0.8)]"
          >
            <div className="bg-[rgba(0,0,0,0.5)] p-3 border-b border-[rgba(0,240,255,0.1)] flex justify-between items-center">
              <div className="flex items-center">
                <div className="w-2 h-2 bg-[#00F0FF] rounded-full mr-2 shadow-[0_0_8px_#00F0FF]" />
                <h4 className="font-orbitron text-[10px] tracking-widest text-[#00F0FF] font-bold">
                  THE ORACLE v3.0
                </h4>
              </div>
              
              <button 
                onClick={toggleListening}
                className={`w-6 h-6 rounded-full flex items-center justify-center transition-all ${isListening ? 'bg-[#FF0055] shadow-[0_0_10px_#FF0055]' : 'bg-[rgba(255,255,255,0.1)] hover:bg-[rgba(255,255,255,0.2)]'}`}
              >
                🎤
              </button>
            </div>
            
            <div className="p-4 min-h-[120px] bg-[rgba(0,240,255,0.02)] relative">
              <div className="absolute inset-0 scanlines opacity-20 mix-blend-overlay pointer-events-none"></div>
              
              <div className="font-mono text-xs text-[#00F0FF] leading-relaxed relative z-10">
                <span className="text-[rgba(255,255,255,0.4)] mr-2">{">"}</span>
                {text}
                {isTyping && <span className="animate-pulse ml-1 inline-block w-2 h-3 bg-[#00F0FF]"></span>}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
