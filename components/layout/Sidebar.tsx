"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useOmniStore } from "../../store/omniStore";

const navItems = [
  { href: "/", label: "COMMAND", icon: "⬡", description: "Command Center" },
  { href: "/charts", label: "CHARTS", icon: "📊", description: "Advanced Charts" },
  { href: "/trading", label: "TRADING", icon: "💰", description: "Trading Terminal" },
  { href: "/derivatives", label: "OPTIONS", icon: "⎈", description: "Options Matrix" },
  { href: "/intelligence", label: "INTEL", icon: "🧠", description: "Market Intelligence" },
  { href: "/wallets", label: "WALLETS", icon: "🏦", description: "Paper Wallet Lab" },
  { href: "/autonomous", label: "AUTO", icon: "🤖", description: "Autonomous Trader" },
  { href: "/alerts", label: "ALERTS", icon: "🔔", description: "Alert Commander" },
  { href: "/settings", label: "CONFIG", icon: "⚙️", description: "System Config" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [isExpanded, setIsExpanded] = useState(false);
  const tickers = useOmniStore((state) => state.tickers);
  const portfolio = useOmniStore((state) => state.portfolio);

  const btcPrice = tickers["BTCUSDT"]?.price || "—";
  const ethPrice = tickers["ETHUSDT"]?.price || "—";

  return (
    <motion.nav
      className="fixed left-0 top-0 h-full z-50 flex flex-col bg-[rgba(5,5,15,0.95)] backdrop-blur-xl border-r border-[rgba(0,240,255,0.1)]"
      animate={{ width: isExpanded ? 220 : 64 }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
      onMouseEnter={() => setIsExpanded(true)}
      onMouseLeave={() => setIsExpanded(false)}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-center border-b border-[rgba(0,240,255,0.1)] px-4">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#00F0FF] to-[#8B00FF] flex items-center justify-center shadow-[0_0_15px_rgba(0,240,255,0.4)]">
          <span className="text-black font-orbitron font-black text-xs">CQ</span>
        </div>
        <AnimatePresence>
          {isExpanded && (
            <motion.span
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              className="ml-3 font-orbitron text-[10px] tracking-widest text-[#00F0FF] whitespace-nowrap"
            >
              CHRONOS QUANTUM
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      {/* Nav Items */}
      <div className="flex-1 flex flex-col py-4 space-y-1 px-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link key={item.href} href={item.href}>
              <div
                className={`relative flex items-center h-11 rounded-lg px-3 transition-all duration-200 group cursor-pointer ${
                  isActive
                    ? "bg-[rgba(0,240,255,0.1)] border border-[rgba(0,240,255,0.3)] shadow-[0_0_10px_rgba(0,240,255,0.1)]"
                    : "hover:bg-[rgba(255,255,255,0.03)] border border-transparent"
                }`}
              >
                {isActive && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 bg-[#00F0FF] rounded-r shadow-[0_0_8px_#00F0FF]" />
                )}
                <span className="text-lg flex-shrink-0 w-8 flex justify-center">{item.icon}</span>
                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ opacity: 0, x: -5 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -5 }}
                      className="ml-3 flex flex-col whitespace-nowrap"
                    >
                      <span className={`font-orbitron text-[9px] tracking-wider ${isActive ? "text-[#00F0FF]" : "text-[rgba(255,255,255,0.6)]"}`}>
                        {item.label}
                      </span>
                      <span className="text-[8px] text-[rgba(255,255,255,0.3)] font-mono">{item.description}</span>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </Link>
          );
        })}
      </div>

      {/* Bottom: Mini Ticker + Portfolio */}
      <div className="border-t border-[rgba(0,240,255,0.1)] p-3 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[8px] font-mono text-[rgba(255,255,255,0.4)]">BTC</span>
          <span className="text-[10px] font-mono text-[#00F0FF] font-bold">${btcPrice}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-[8px] font-mono text-[rgba(255,255,255,0.4)]">ETH</span>
          <span className="text-[10px] font-mono text-[#8B00FF] font-bold">${ethPrice}</span>
        </div>
        
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="pt-2 border-t border-[rgba(255,255,255,0.05)]"
            >
              <span className="text-[8px] font-mono text-[rgba(255,255,255,0.3)] block">PORTFOLIO</span>
              <span className="text-[11px] font-orbitron text-white font-bold">
                ${portfolio.usdt.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.nav>
  );
}
