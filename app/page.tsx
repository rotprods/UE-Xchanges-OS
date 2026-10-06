"use client";

import React, { useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import { motion, useScroll, useTransform } from "framer-motion";
import GasTracker from "../components/dom/GasTracker";
import VolumeHeatmap from "../components/dom/VolumeHeatmap";
import AlertFeed from "../components/dom/AlertFeed";
import FearGreedIndex from "../components/dom/FearGreedIndex";
import TickerTape from "../components/dom/TickerTape";
import ArbitrageScanner from "../components/dom/ArbitrageScanner";
import PlayerCard from "../components/dom/PlayerCard";
import HoloLeaderboard from "../components/dom/HoloLeaderboard";
import { useOmniStore } from "../store/omniStore";

const QuantumCanvas = dynamic(() => import("../components/canvas/QuantumCanvas"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full bg-[#05050A] flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-t-transparent border-[#00F0FF] rounded-full animate-spin" />
    </div>
  ),
});

const OrderBookCanvas = dynamic(() => import("../components/canvas/OrderBookCanvas"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center text-[#8B00FF]">
      <div className="w-8 h-8 border-2 border-t-transparent border-[#8B00FF] rounded-full animate-spin" />
    </div>
  ),
});

export default function CommandCenter() {
  const { tickers, stats, pulseTrigger, mempoolEvents } = useOmniStore();
  const portfolio = useOmniStore((state) => state.portfolio);
  const panicLevel = useOmniStore((state) => state.panicLevel);
  const dashboardRef = useRef<HTMLDivElement>(null);

  const totalPortfolioValue =
    portfolio.usdt +
    Object.entries(portfolio.assets).reduce((acc, [sym, qty]) => {
      const ticker = tickers[sym];
      return acc + (ticker ? qty * parseFloat(ticker.price) : 0);
    }, 0);

  // Scroll-driven hero fade
  const { scrollY } = useScroll();
  const heroOpacity = useTransform(scrollY, [0, 400], [1, 0]);
  const heroScale = useTransform(scrollY, [0, 400], [1, 0.92]);
  const globeY = useTransform(scrollY, [0, 600], [0, -100]);
  const dashOpacity = useTransform(scrollY, [200, 500], [0, 1]);
  const dashY = useTransform(scrollY, [200, 500], [60, 0]);

  const scrollToDashboard = () => {
    dashboardRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="relative min-h-screen">

      {/* ─────────────────────────── HERO SECTION ─────────────────────────── */}
      <motion.section
        className="relative h-screen flex flex-col items-center justify-center overflow-hidden"
        style={{ opacity: heroOpacity, scale: heroScale }}
      >
        {/* 3D Globe — full hero */}
        <motion.div
          className="absolute inset-0 w-full h-full z-0"
          style={{ y: globeY, opacity: panicLevel > 0.5 ? 0.7 : 0.5 }}
        >
          <QuantumCanvas txRate={stats.txsPerSecond} pulseTrigger={pulseTrigger} />
        </motion.div>

        {/* Scanlines overlay */}
        <div className="absolute inset-0 scanlines pointer-events-none z-10 opacity-20" />

        {/* Vignette */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_transparent_30%,_rgba(5,5,10,0.8)_100%)] z-10 pointer-events-none" />

        {/* Hero Text */}
        <div className="relative z-20 flex flex-col items-center text-center px-6">
          <motion.div
            initial={{ opacity: 0, y: -30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, ease: "easeOut" }}
          >
            <p className="font-mono text-[10px] tracking-[0.5em] text-[rgba(0,240,255,0.6)] mb-4">
              CHRONOS QUANTUM v1.0 — REAL-TIME INTELLIGENCE TERMINAL
            </p>
            <h1
              className="font-orbitron font-black text-5xl md:text-7xl leading-tight mb-4"
              style={{
                background: "linear-gradient(135deg, #00F0FF 0%, #8B00FF 50%, #FF0055 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
                textShadow: "none",
                filter: "drop-shadow(0 0 40px rgba(0,240,255,0.3))",
              }}
            >
              CHRONOS
              <br />
              QUANTUM
            </h1>
            <p className="font-mono text-sm text-[rgba(255,255,255,0.5)] max-w-md mx-auto leading-relaxed">
              Institutional-grade crypto intelligence. Real-time data. Autonomous AI. Zero latency.
            </p>
          </motion.div>

          {/* Live ticker mini-stats */}
          <motion.div
            className="mt-8 flex items-center gap-6 flex-wrap justify-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8, duration: 1 }}
          >
            {["BTCUSDT", "ETHUSDT", "SOLUSDT"].map((sym) => {
              const t = tickers[sym];
              if (!t) return null;
              const change = t.change ?? 0;
              return (
                <div key={sym} className="flex flex-col items-center">
                  <span className="font-mono text-[9px] text-[rgba(255,255,255,0.4)]">
                    {sym.replace("USDT", "")}
                  </span>
                  <span className="font-orbitron text-sm font-bold text-white">
                    ${parseFloat(t.price).toLocaleString(undefined, { maximumFractionDigits: 2 })}
                  </span>
                  <span
                    className={`font-mono text-[9px] ${change >= 0 ? "text-[#00FF66]" : "text-[#FF0055]"}`}
                  >
                    {change >= 0 ? "+" : ""}{change.toFixed(2)}%
                  </span>
                </div>
              );
            })}
          </motion.div>

          {/* Scroll CTA */}
          <motion.button
            onClick={scrollToDashboard}
            className="mt-12 flex flex-col items-center gap-2 group cursor-pointer"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.5 }}
          >
            <span className="font-mono text-[10px] tracking-[0.3em] text-[rgba(0,240,255,0.5)] group-hover:text-[#00F0FF] transition-colors">
              SCROLL TO OPEN COMMAND CENTER
            </span>
            <motion.div
              animate={{ y: [0, 8, 0] }}
              transition={{ repeat: Infinity, duration: 1.8, ease: "easeInOut" }}
              className="w-6 h-6 border-b-2 border-r-2 border-[rgba(0,240,255,0.4)] rotate-45 group-hover:border-[#00F0FF] transition-colors"
            />
          </motion.button>
        </div>
      </motion.section>

      {/* ─────────────────────────── DASHBOARD SECTION ─────────────────────────── */}
      <motion.div
        ref={dashboardRef}
        className="relative z-10 bg-[#05050A]"
        style={{ opacity: dashOpacity, y: dashY }}
      >
        {/* Fixed globe behind dashboard (subtle) */}
        <div
          className="fixed inset-0 w-full h-full z-0 pointer-events-none transition-opacity duration-1000"
          style={{ opacity: panicLevel > 0.5 ? 0.15 : 0.08 }}
        >
          <QuantumCanvas txRate={stats.txsPerSecond} pulseTrigger={pulseTrigger} />
        </div>

        {/* Scanlines */}
        <div className="fixed inset-0 scanlines pointer-events-none z-30 opacity-10" />

        {/* Ticker Tape */}
        <div className="sticky top-0 z-40">
          <TickerTape />
        </div>

        <div className="relative z-10 p-6 space-y-6">

          {/* Player Card */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.7 }}
          >
            <PlayerCard />
          </motion.div>

          {/* Hero Summary Cards */}
          <motion.div
            className="grid grid-cols-2 md:grid-cols-4 gap-4"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.7, delay: 0.1 }}
          >
            <SummaryCard
              label="PORTFOLIO VALUE"
              value={`$${totalPortfolioValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
              color="#00F0FF"
            />
            <SummaryCard
              label="24H VOLUME"
              value={`$${(stats.totalVolume24h / 1e9).toFixed(2)}B`}
              color="#8B00FF"
            />
            <SummaryCard
              label="TX / SEC"
              value={stats.txsPerSecond.toString()}
              color="#FF5500"
            />
            <SummaryCard
              label="MEMPOOL FEE"
              value={`${stats.gasGwei} sat/vB`}
              color="#00FF66"
            />
          </motion.div>

          {/* Fear & Greed */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.6, delay: 0.15 }}
          >
            <FearGreedIndex />
          </motion.div>

          {/* Main Dashboard Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 items-start auto-rows-max">
            {/* Widget 1: Bitcoin Mempool */}
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.2 }}
              transition={{ duration: 0.8 }}
            >
              <GasTracker gasGwei={stats.gasGwei} txRate={stats.txsPerSecond} />
            </motion.div>

            {/* Widget 2: Volume Heatmap */}
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.2 }}
              transition={{ duration: 0.8, delay: 0.1 }}
            >
              <VolumeHeatmap tickers={tickers} totalVolume={stats.totalVolume24h} />
            </motion.div>

            {/* Widget 3: The Dark Forest (Mempool Radar) */}
            <motion.div
              className="xl:col-span-1 h-full min-h-[340px] border border-[rgba(255,85,0,0.3)] bg-[rgba(20,5,5,0.4)] backdrop-blur-md rounded-2xl p-6 relative overflow-hidden flex flex-col"
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.2 }}
              transition={{ duration: 0.8, delay: 0.2 }}
            >
              <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-[rgba(255,85,0,0.15)] to-transparent pointer-events-none" />
              <div className="flex justify-between items-center mb-4 z-10">
                <h3 className="font-orbitron font-bold text-[#FF5500] tracking-wider text-sm">
                  THE DARK FOREST
                </h3>
                <div className="w-2 h-2 bg-[#FF5500] rounded-full animate-pulse shadow-[0_0_10px_#FF5500]" />
              </div>
              <div className="flex-1 overflow-hidden relative z-10">
                <div className="absolute inset-0 flex flex-col space-y-2 overflow-hidden">
                  {mempoolEvents.slice(0, 10).map((ev, i) => (
                    <motion.div
                      key={ev.hash + ev.time}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1 - i * 0.1, x: 0 }}
                      className="flex justify-between items-center text-[10px] font-mono border-b border-[rgba(255,85,0,0.2)] pb-1"
                    >
                      <span className="text-[rgba(255,255,255,0.7)] truncate w-24">
                        {ev.hash.substring(0, 10)}...
                      </span>
                      <span className="text-[#00F0FF]">{ev.network}</span>
                      <span className="text-[#FF5500] font-bold">{ev.gas} sat/vB</span>
                    </motion.div>
                  ))}
                  {mempoolEvents.length === 0 && (
                    <div className="flex items-center justify-center h-full">
                      <span className="font-mono text-[10px] text-[rgba(255,255,255,0.3)] animate-pulse">
                        SCANNING MEMPOOL...
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>

            {/* Widget 4: The Wall (Orderbook Hologram) */}
            <motion.div
              className="md:col-span-2 xl:col-span-2 h-[400px] border border-[rgba(139,0,255,0.3)] bg-[rgba(15,5,25,0.4)] backdrop-blur-md rounded-2xl relative flex items-center justify-center overflow-hidden"
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.2 }}
              transition={{ duration: 0.8, delay: 0.3 }}
            >
              <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom,_var(--tw-gradient-stops))] from-[rgba(139,0,255,0.15)] to-transparent pointer-events-none z-10" />
              <div className="absolute top-6 left-6 z-10">
                <h3 className="font-orbitron font-bold text-[#8B00FF] tracking-wider text-sm flex items-center">
                  THE WALL <span className="ml-2 w-2 h-2 rounded-full bg-[#8B00FF] animate-pulse" />
                </h3>
                <p className="font-mono text-[10px] text-[rgba(255,255,255,0.5)] mt-1">
                  Live Order Book Hologram
                </p>
              </div>
              <div className="absolute inset-0 z-0">
                <OrderBookCanvas />
              </div>
            </motion.div>

            {/* Widget 5: Global Event Feed */}
            <motion.div
              className="md:col-span-2 xl:col-span-1 h-[400px] border border-[rgba(0,240,255,0.3)] bg-[rgba(5,15,25,0.4)] backdrop-blur-md rounded-2xl p-6 relative overflow-hidden"
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.2 }}
              transition={{ duration: 0.8, delay: 0.4 }}
            >
              <AlertFeed />
            </motion.div>
          </div>

          {/* Arbitrage Scanner */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.8, delay: 0.1 }}
          >
            <ArbitrageScanner />
          </motion.div>

          {/* Session Leaderboard */}
          <motion.div
            initial={{ opacity: 0, scale: 0.97 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.8 }}
          >
            <HoloLeaderboard />
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="border rounded-xl p-4 backdrop-blur-md relative overflow-hidden"
      style={{ borderColor: `${color}33`, backgroundColor: `${color}08` }}
    >
      <div
        className="absolute inset-0 opacity-10"
        style={{
          background: `radial-gradient(ellipse at bottom, ${color}22, transparent)`,
        }}
      />
      <span
        className="block font-mono text-[9px] tracking-wider relative z-10"
        style={{ color: `${color}99` }}
      >
        {label}
      </span>
      <span
        className="block font-orbitron text-lg font-bold mt-1 relative z-10"
        style={{ color }}
      >
        {value}
      </span>
    </motion.div>
  );
}
