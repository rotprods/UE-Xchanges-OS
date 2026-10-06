"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useOmniStore } from "../../store/omniStore";

type FilterType = "ALL" | "whale" | "rekt" | "network";

const FILTER_LABELS: { id: FilterType; label: string }[] = [
  { id: "ALL",     label: "ALL"     },
  { id: "whale",   label: "WHALE"   },
  { id: "rekt",    label: "REKT"    },
  { id: "network", label: "NETWORK" },
];

const TYPE_ICONS: Record<string, string> = {
  whale:   "🐋",
  rekt:    "💀",
  network: "🌐",
  system:  "⚙️",
};

export default function AlertFeed() {
  const toasts = useOmniStore((state) => state.toasts);
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeFilter, setActiveFilter] = useState<FilterType>("ALL");

  const allToasts = [...toasts].reverse();
  const displayToasts = (
    activeFilter === "ALL"
      ? allToasts
      : allToasts.filter((t) => t.type === activeFilter)
  ).slice(0, 50);

  const containerClasses = isExpanded
    ? "fixed inset-4 z-50 bg-[rgba(5,15,25,0.95)] backdrop-blur-xl border border-[rgba(0,240,255,0.5)] rounded-2xl p-6 flex flex-col shadow-[0_0_50px_rgba(0,240,255,0.2)]"
    : "w-full h-full flex flex-col";

  return (
    <div className={containerClasses}>
      {/* Header */}
      <div className="flex justify-between items-center mb-3 border-b border-[rgba(0,240,255,0.1)] pb-2">
        <h3 className="font-orbitron font-bold text-xs tracking-widest text-[#00F0FF] flex items-center gap-2">
          <span className="w-2 h-2 bg-[#FF0055] rounded-full animate-pulse" />
          GLOBAL EVENT FEED
          {/* Event count badge */}
          <span className="ml-1 px-1.5 py-0.5 rounded text-[8px] font-mono bg-[rgba(0,240,255,0.1)] border border-[rgba(0,240,255,0.2)] text-[#00F0FF]">
            {toasts.length}
          </span>
        </h3>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-[10px] font-mono text-[rgba(0,240,255,0.6)] hover:text-[#00F0FF] transition-colors px-2 py-1 border border-[rgba(0,240,255,0.2)] rounded bg-[rgba(0,240,255,0.05)]"
        >
          {isExpanded ? "COLLAPSE [ - ]" : "EXPAND [ + ]"}
        </button>
      </div>

      {/* Filter Buttons */}
      <div className="flex items-center gap-1 mb-3">
        {FILTER_LABELS.map(({ id, label }) => {
          const isActive = activeFilter === id;
          return (
            <button
              key={id}
              onClick={() => setActiveFilter(id)}
              className={`px-2 py-0.5 text-[8px] font-orbitron font-bold rounded border transition-all ${
                isActive
                  ? "border-[rgba(0,240,255,0.6)] bg-[rgba(0,240,255,0.1)] text-[#00F0FF]"
                  : "border-[rgba(255,255,255,0.1)] text-[rgba(255,255,255,0.3)] hover:text-white hover:border-[rgba(255,255,255,0.3)]"
              }`}
            >
              {label}
            </button>
          );
        })}
      </div>

      {/* Event List */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-2 scroll-container">
        <AnimatePresence>
          {displayToasts.map((toast) => {
            const isWhale = toast.type === "whale";
            const isRekt = toast.type === "rekt";

            let bgColor = "bg-[rgba(255,85,0,0.05)]";
            let borderColor = "border-[rgba(255,85,0,0.3)]";
            let textColor = "text-[#FF5500]";

            if (isWhale) {
              bgColor = "bg-[rgba(0,240,255,0.05)]";
              borderColor = "border-[rgba(0,240,255,0.3)]";
              textColor = "text-[#00F0FF]";
            } else if (isRekt) {
              bgColor = "bg-[rgba(255,0,85,0.1)]";
              borderColor = "border-[rgba(255,0,85,0.5)]";
              textColor = "text-[#FF0055]";
            } else if (toast.type === "network") {
              bgColor = "bg-[rgba(139,0,255,0.05)]";
              borderColor = "border-[rgba(139,0,255,0.3)]";
              textColor = "text-[#8B00FF]";
            }

            const icon = TYPE_ICONS[toast.type] ?? "ℹ️";

            return (
              <motion.div
                key={toast.id}
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.3 }}
                className={`border ${borderColor} ${bgColor} p-3 rounded w-full relative overflow-hidden ${isRekt ? "animate-pulse" : ""}`}
              >
                <div className="relative z-10 flex flex-col">
                  <div className="flex justify-between items-center mb-1">
                    <h4 className={`font-orbitron font-bold text-[10px] tracking-widest ${textColor} flex items-center gap-1.5`}>
                      <span className="text-[11px]">{icon}</span>
                      <span className={`w-1.5 h-1.5 rounded-full ${isWhale ? "bg-[#00F0FF]" : isRekt ? "bg-[#FF0055]" : "bg-[#FF5500]"}`} />
                      {toast.title}
                    </h4>
                    <span className="font-mono text-[8px] text-[rgba(255,255,255,0.4)]">EVENT</span>
                  </div>
                  <p className={`font-mono text-[10px] sm:text-xs leading-tight ${isRekt ? "text-[#FF0055] font-bold" : "text-[rgba(255,255,255,0.8)]"}`}>
                    {toast.message}
                  </p>
                </div>
              </motion.div>
            );
          })}
          {displayToasts.length === 0 && (
            <div className="flex items-center justify-center h-full text-[10px] font-mono text-[rgba(255,255,255,0.3)]">
              NO ANOMALIES DETECTED YET
            </div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
