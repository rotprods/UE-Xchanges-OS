"use client";

import React, { useState, useEffect } from "react";
import { audioController } from "../../utils/audioController";
import { useOmniStore } from "../../store/omniStore";

interface HeaderProps {
  txRate: number;
  gasGwei: number;
}

export default function Header({ txRate, gasGwei }: HeaderProps) {
  const audioEnabled = useOmniStore((state) => state.audioEnabled);
  const toggleAudio = useOmniStore((state) => state.toggleAudio);
  const [ping, setPing] = useState(12);

  // Simulate subtle ping fluctuations
  useEffect(() => {
    const interval = setInterval(() => {
      setPing((prev) => Math.max(8, Math.min(35, prev + Math.round((Math.random() - 0.5) * 4))));
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleAudioToggle = () => {
    const nextState = audioController.toggle();
    toggleAudio(); // Sync with Zustand
    if (nextState) {
      audioController.playTick(1000, 0.1, 0.08);
    }
  };

  return (
    <header className="fixed top-0 left-0 w-full z-50 px-6 py-4 flex justify-between items-center border-b border-[rgba(0,240,255,0.1)] bg-[rgba(5,5,10,0.55)] backdrop-blur-md">
      {/* Brand Title */}
      <div className="flex items-center space-x-3">
        <div className="w-2.5 h-2.5 bg-[#00F0FF] rounded-full shadow-glow animate-pulse" />
        <h1 className="font-orbitron text-lg font-black tracking-widest text-[#00F0FF] text-glow select-none">
          CHRONOS <span className="text-[#8B00FF]">//</span> QUANTUM
        </h1>
      </div>

      {/* Grid Dashboard Status Info */}
      <div className="hidden md:flex space-x-8 font-mono text-xs text-[rgba(255,255,255,0.6)]">
        <div className="flex flex-col">
          <span className="text-[10px] text-[rgba(0,240,255,0.5)]">DATA OVERLAY</span>
          <span className="text-white">WEBSOCKETS [LIVE]</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] text-[rgba(0,240,255,0.5)]">TX FEED</span>
          <span className="text-white">{txRate} TX/S</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] text-[rgba(0,240,255,0.5)]">GAS RATE</span>
          <span className="text-white">{gasGwei} GWEI</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] text-[rgba(0,240,255,0.5)]">LATENCY</span>
          <span className="text-[#00FF66]">{ping} MS</span>
        </div>
      </div>

      {/* Interaction Controls */}
      <div className="flex items-center space-x-4">
        {/* Network Status LED */}
        <div className="flex items-center space-x-2 bg-[rgba(0,240,255,0.05)] px-3 py-1 rounded border border-[rgba(0,240,255,0.15)] font-mono text-[10px] text-[#00F0FF]">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00FF66] opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-[#00FF66]"></span>
          </span>
          <span>QUANTUM_CORE_ONLINE</span>
        </div>

        {/* Audio Toggle button */}
        <button
          onClick={handleAudioToggle}
          onMouseEnter={() => audioController.playTick(600, 0.03, 0.01)}
          className={`flex items-center justify-center w-8 h-8 rounded border transition-all duration-300 ${
            audioEnabled
              ? "bg-[rgba(0,240,255,0.15)] border-[#00F0FF] text-[#00F0FF] shadow-glow"
              : "bg-transparent border-[rgba(255,255,255,0.2)] text-[rgba(255,255,255,0.5)] hover:border-[rgba(0,240,255,0.4)]"
          }`}
          title={audioEnabled ? "Mute Audio" : "Unmute Audio"}
        >
          {audioEnabled ? (
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.114 5.636a9 9 0 0 1 0 12.728M16.463 8.288a5.25 5.25 0 0 1 0 7.424M6.75 8.25l4.72-4.72a.75.75 0 0 1 1.28.53v15.88a.75.75 0 0 1-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.009 9.009 0 0 1 2.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75Z" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
              <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 9.75 19.5 12m0 0 2.25 2.25M19.5 12l2.25-2.25M19.5 12l-2.25 2.25m-10.5-6 4.72-4.72a.75.75 0 0 1 1.28.53v15.88a.75.75 0 0 1-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.009 9.009 0 0 1 2.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75Z" />
            </svg>
          )}
        </button>
      </div>
    </header>
  );
}
