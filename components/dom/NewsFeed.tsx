"use client";

import React, { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useOmniStore } from "../../store/omniStore";
import type { NewsItem } from "../../store/omniStore";

// ─── Helpers ────────────────────────────────────────────────────────────────

const BULLISH_KEYWORDS = [
  "surge", "bull", "rally", "rise", "gain", "up", "high", "record",
  "breakout", "pump", "soar", "bullish", "growth", "boom", "moon",
];
const BEARISH_KEYWORDS = [
  "drop", "bear", "crash", "fall", "loss", "down", "low", "decline",
  "dump", "plunge", "bearish", "slump", "collapse", "sell-off",
];

type Sentiment = "BULLISH" | "BEARISH" | "NEUTRAL";

function getSentiment(title: string): Sentiment {
  const lower = title.toLowerCase();
  const bull = BULLISH_KEYWORDS.some((k) => lower.includes(k));
  const bear = BEARISH_KEYWORDS.some((k) => lower.includes(k));
  if (bull && !bear) return "BULLISH";
  if (bear && !bull) return "BEARISH";
  return "NEUTRAL";
}

function getRelativeTime(unixSeconds: number): string {
  if (!unixSeconds) return "UNKNOWN";
  const diffMs = Date.now() - unixSeconds * 1000;
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins} min ago`;
  const diffHrs = Math.floor(diffMins / 60);
  if (diffHrs < 24) return `${diffHrs}h ago`;
  return `${Math.floor(diffHrs / 24)}d ago`;
}

const SENTIMENT_STYLES: Record<Sentiment, { label: string; color: string; bg: string }> = {
  BULLISH: { label: "BULLISH", color: "#00FF66", bg: "rgba(0,255,102,0.12)" },
  BEARISH: { label: "BEARISH", color: "#FF0055", bg: "rgba(255,0,85,0.12)" },
  NEUTRAL: { label: "NEUTRAL", color: "#8B00FF", bg: "rgba(139,0,255,0.12)" },
};

// ─── Ticker marquee sub-component ─────────────────────────────────────────────

function HeadlineTicker({ items }: { items: NewsItem[] }) {
  const tickerRef = useRef<HTMLDivElement>(null);

  return (
    <div className="relative overflow-hidden border-t border-[rgba(0,240,255,0.15)] pt-2 mt-2">
      <span className="font-orbitron text-[8px] text-[#00F0FF] mr-3 shrink-0">
        ◈ LIVE FEED
      </span>
      <div className="overflow-hidden">
        <div
          ref={tickerRef}
          className="flex whitespace-nowrap"
          style={{ animation: "ticker-scroll 40s linear infinite" }}
        >
          {[...items, ...items].map((item, i) => (
            <span
              key={`${item.id}-${i}`}
              className="font-mono text-[10px] text-[rgba(255,255,255,0.55)] mr-12 cursor-pointer hover:text-white transition-colors"
              onClick={() => window.open(item.url, "_blank", "noopener noreferrer")}
            >
              <span className="text-[#00F0FF] mr-1">◈</span>
              {item.title}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function NewsFeed() {
  const newsItems = useOmniStore((state) => state.newsItems);
  const [now, setNow] = useState(Date.now());

  // Refresh relative timestamps every 30s
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 30000);
    return () => clearInterval(id);
  }, []);

  const isLoading = newsItems.length === 0;

  return (
    <div className="border border-[rgba(139,0,255,0.3)] bg-[rgba(5,5,15,0.5)] backdrop-blur-md rounded-2xl p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h4 className="font-orbitron text-[9px] tracking-widest text-[#8B00FF] flex items-center gap-2">
          <span className="w-1.5 h-1.5 bg-[#8B00FF] rounded-full animate-pulse" />
          CRYPTO INTEL FEED
        </h4>
        <span className="font-mono text-[9px] text-[rgba(255,255,255,0.25)]">
          {isLoading ? "FETCHING INTEL..." : `${newsItems.length} SIGNALS`}
        </span>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className="border border-[rgba(139,0,255,0.15)] rounded-xl p-3 animate-pulse space-y-2"
            >
              <div className="h-2 w-16 rounded bg-[rgba(255,255,255,0.07)]" />
              <div className="h-3 w-full rounded bg-[rgba(255,255,255,0.05)]" />
              <div className="h-3 w-3/4 rounded bg-[rgba(255,255,255,0.04)]" />
            </div>
          ))}
        </div>
      )}

      {/* News cards */}
      {!isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-3">
          <AnimatePresence>
            {newsItems.map((item) => {
              const sentiment = getSentiment(item.title);
              const style = SENTIMENT_STYLES[sentiment];
              const relTime = getRelativeTime(item.publishedAt);

              return (
                <motion.article
                  key={item.id}
                  initial={{ opacity: 0, scale: 0.96 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  onClick={() => window.open(item.url, "_blank", "noopener noreferrer")}
                  className="group border border-[rgba(139,0,255,0.2)] bg-[rgba(10,5,20,0.6)] rounded-xl p-3 cursor-pointer flex flex-col gap-2 hover:border-[rgba(139,0,255,0.5)] hover:bg-[rgba(20,5,35,0.7)] transition-all duration-200"
                >
                  {/* Meta row */}
                  <div className="flex items-center justify-between gap-1 flex-wrap">
                    <span className="font-mono text-[8px] text-[rgba(255,255,255,0.35)] uppercase truncate max-w-[80px]">
                      {item.source}
                    </span>
                    <span className="font-mono text-[8px] text-[rgba(255,255,255,0.25)]">
                      {relTime}
                    </span>
                  </div>

                  {/* Title */}
                  <p className="font-mono text-[10px] leading-snug text-[rgba(255,255,255,0.8)] group-hover:text-white line-clamp-3 transition-colors">
                    {item.title}
                  </p>

                  {/* Sentiment badge */}
                  <div className="mt-auto pt-1">
                    <span
                      className="font-orbitron text-[7px] font-bold px-1.5 py-0.5 rounded"
                      style={{ color: style.color, backgroundColor: style.bg, border: `1px solid ${style.color}44` }}
                    >
                      {style.label}
                    </span>
                  </div>

                  {/* Category tags */}
                  {item.categories && (
                    <div className="flex flex-wrap gap-1">
                      {item.categories
                        .split("|")
                        .slice(0, 2)
                        .map((cat) => (
                          <span
                            key={cat}
                            className="font-mono text-[7px] text-[rgba(0,240,255,0.5)] border border-[rgba(0,240,255,0.15)] rounded px-1"
                          >
                            {cat.trim()}
                          </span>
                        ))}
                    </div>
                  )}
                </motion.article>
              );
            })}
          </AnimatePresence>
        </div>
      )}

      {/* Scrolling headline ticker */}
      {!isLoading && newsItems.length > 0 && (
        <HeadlineTicker items={newsItems} />
      )}
    </div>
  );
}
