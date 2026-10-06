"use client";

import React, { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useOmniStore } from "../../store/omniStore";

export default function AlertToasts() {
  const toasts = useOmniStore((state) => state.toasts);
  const removeToast = useOmniStore((state) => state.removeToast);

  // Auto-remove toasts after 5 seconds
  useEffect(() => {
    if (toasts.length === 0) return;
    
    const timeouts = toasts.map((toast) => {
      return setTimeout(() => {
        removeToast(toast.id);
      }, 5000);
    });

    return () => {
      timeouts.forEach(clearTimeout);
    };
  }, [toasts, removeToast]);

  return (
    <div className="fixed top-24 right-6 z-50 flex flex-col space-y-3 pointer-events-none">
      <AnimatePresence>
        {toasts.map((toast) => {
          const isWhale = toast.type === "whale";
          const isRekt = toast.type === "rekt";
          
          let bgColor = "bg-[rgba(255,85,0,0.15)]";
          let borderColor = "border-[#FF5500]";
          let textColor = "text-[#FF5500]";
          
          if (isWhale) {
            bgColor = "bg-[rgba(0,240,255,0.15)]";
            borderColor = "border-[#00F0FF]";
            textColor = "text-[#00F0FF]";
          } else if (isRekt) {
            bgColor = "bg-[rgba(255,0,85,0.2)]";
            borderColor = "border-[#FF0055]";
            textColor = "text-[#FF0055]";
          }

          return (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, x: 50, scale: 0.9 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 50, scale: 0.9 }}
              transition={{ duration: 0.3, type: "spring", stiffness: 300, damping: 25 }}
              className={`backdrop-blur-md border ${borderColor} ${bgColor} p-4 rounded shadow-[0_0_15px_rgba(0,0,0,0.5)] w-72 md:w-80 relative overflow-hidden ${isRekt ? 'animate-pulse' : ''}`}
            >
              <div className="absolute inset-0 scanlines opacity-30 mix-blend-overlay"></div>
              
              <div className="relative z-10 flex flex-col">
                <div className="flex justify-between items-center mb-1">
                  <h4 className={`font-orbitron font-bold text-[10px] tracking-widest ${textColor} flex items-center`}>
                    <span className={`w-1.5 h-1.5 rounded-full mr-2 animate-pulse ${isWhale ? 'bg-[#00F0FF]' : isRekt ? 'bg-[#FF0055]' : 'bg-[#FF5500]'}`}></span>
                    {toast.title}
                  </h4>
                  <span className="font-mono text-[8px] text-[rgba(255,255,255,0.4)]">NOW</span>
                </div>
                <p className={`font-mono text-xs leading-tight ${isRekt ? 'text-[#FF0055] font-bold' : 'text-white'}`}>
                  {toast.message}
                </p>
              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
