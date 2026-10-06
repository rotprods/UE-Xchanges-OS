import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useOmniStore } from "../../store/omniStore";

export default function WhaleSonar() {
  const whaleAlerts = useOmniStore((state) => state.whaleAlerts);
  const audioEnabled = useOmniStore((state) => state.audioEnabled);
  const [sonarAngle, setSonarAngle] = useState(0);

  // Radar sweep animation
  useEffect(() => {
    let animationFrameId: number;
    const animate = () => {
      setSonarAngle((prev) => (prev + 2) % 360);
      animationFrameId = requestAnimationFrame(animate);
    };
    animate();
    return () => cancelAnimationFrame(animationFrameId);
  }, []);

  return (
    <div className="h-full w-full flex flex-col relative z-10">
      <div className="flex justify-between items-center mb-6">
        <h3 className="font-orbitron font-bold text-[#00F0FF] tracking-wider text-sm">
          WHALE SONAR
        </h3>
        <div className="flex items-center space-x-2">
          <span className="font-mono text-[9px] text-[rgba(255,255,255,0.4)]">ON-CHAIN RADAR</span>
          <div className="w-2 h-2 bg-[#00F0FF] rounded-full shadow-[0_0_8px_#00F0FF]" />
        </div>
      </div>

      <div className="flex-1 flex flex-col lg:flex-row items-center gap-6 overflow-hidden">
        
        {/* Radar Graphic */}
        <div className="relative w-32 h-32 flex-shrink-0 border border-[rgba(0,240,255,0.3)] rounded-full flex items-center justify-center overflow-hidden bg-[rgba(0,20,30,0.5)]">
          <div className="absolute inset-0 rounded-full border border-[rgba(0,240,255,0.1)] m-4" />
          <div className="absolute inset-0 rounded-full border border-[rgba(0,240,255,0.05)] m-8" />
          {/* Radar Sweep */}
          <div 
            className="absolute top-1/2 left-1/2 w-[50%] h-[50%] origin-top-left"
            style={{ 
              transform: `rotate(${sonarAngle}deg)`,
              background: 'conic-gradient(from 180deg, rgba(0,240,255,0) 0%, rgba(0,240,255,0.5) 100%)',
            }}
          />
          <div className="w-1 h-1 bg-[#00F0FF] rounded-full z-10 shadow-glow" />
          
          {/* Render blips based on active alerts */}
          {whaleAlerts.slice(0, 3).map((alert, i) => {
            // Randomish position based on ID string characters
            const angle = (alert.id.charCodeAt(4) * 15) % 360;
            const distance = 20 + (alert.id.charCodeAt(5) % 30);
            const top = 50 + distance * Math.sin(angle * Math.PI / 180);
            const left = 50 + distance * Math.cos(angle * Math.PI / 180);
            
            return (
              <motion.div 
                key={`blip-${alert.id}`}
                className="absolute w-2 h-2 rounded-full bg-white shadow-[0_0_10px_#FFFFFF]"
                style={{ top: `${top}%`, left: `${left}%` }}
                initial={{ opacity: 1, scale: 2 }}
                animate={{ opacity: 0, scale: 0 }}
                transition={{ duration: 4, ease: "easeOut" }}
              />
            );
          })}
        </div>

        {/* Alert List */}
        <div className="flex-1 w-full overflow-hidden flex flex-col space-y-2">
          <AnimatePresence>
            {whaleAlerts.slice(0, 4).map((alert) => (
              <motion.div 
                key={alert.id}
                initial={{ opacity: 0, x: 20, backgroundColor: "rgba(0,240,255,0.2)" }}
                animate={{ opacity: 1, x: 0, backgroundColor: "rgba(0,0,0,0)" }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.5 }}
                className="flex flex-col border border-[rgba(255,255,255,0.05)] rounded p-2 text-[10px] font-mono bg-[rgba(5,5,10,0.5)]"
              >
                <div className="flex justify-between items-center mb-1">
                  <span className="text-white font-bold">{alert.token} TRANSFER</span>
                  <span className="text-[#00F0FF]">{alert.amountUsd}</span>
                </div>
                <div className="flex justify-between text-[rgba(255,255,255,0.4)]">
                  <span className="truncate max-w-[100px]">{alert.from}</span>
                  <span>➜</span>
                  <span className="truncate max-w-[100px]">{alert.to}</span>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          {whaleAlerts.length === 0 && (
            <div className="h-full flex items-center justify-center text-[10px] text-[rgba(255,255,255,0.3)] font-mono">
              SCANNING DEEP LIQUIDITY...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
