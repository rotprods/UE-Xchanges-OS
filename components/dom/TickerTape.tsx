'use client';

import React from 'react';
import { useOmniStore } from '../../store/omniStore';

const SEPARATOR = (
  <span className="mx-3 text-[#00F0FF] opacity-50 select-none">◆</span>
);

export default function TickerTape() {
  const tickers = useOmniStore((state) => state.tickers);

  const entries = Object.values(tickers);

  if (entries.length === 0) {
    return (
      <div className="h-8 border-b border-[rgba(0,240,255,0.15)] bg-black flex items-center px-4">
        <span className="font-mono text-[9px] text-[rgba(255,255,255,0.3)] tracking-widest animate-pulse">
          AWAITING_MARKET_DATA...
        </span>
      </div>
    );
  }

  const tickerItems = entries.map((ticker, i) => {
    const price = parseFloat(ticker.price);
    const change = ticker.change ?? 0;
    const isPositive = change >= 0;
    const changeColor = isPositive ? '#00FF66' : '#FF0055';
    const changePrefix = isPositive ? '+' : '';
    const symbol = ticker.symbol.replace('USDT', '').replace('USD', '');

    return (
      <React.Fragment key={`${ticker.symbol}-${i}`}>
        <span className="inline-flex items-center gap-1.5 shrink-0 px-1">
          <span className="font-orbitron text-[9px] font-bold text-white tracking-wider">
            {symbol}
          </span>
          <span className="font-mono text-[9px] text-[rgba(255,255,255,0.8)]">
            ${price >= 1000
              ? price.toLocaleString(undefined, { maximumFractionDigits: 0 })
              : price >= 1
              ? price.toFixed(2)
              : price.toFixed(4)}
          </span>
          <span
            className="font-mono text-[9px] font-bold"
            style={{ color: changeColor }}
          >
            {changePrefix}{change.toFixed(2)}%
          </span>
        </span>
        {SEPARATOR}
      </React.Fragment>
    );
  });

  return (
    <div
      className="h-8 border-b border-[rgba(0,240,255,0.15)] bg-black overflow-hidden relative"
      aria-label="Live market ticker"
    >
      {/* Fade edges */}
      <div className="absolute left-0 top-0 h-full w-8 z-10 pointer-events-none"
        style={{ background: 'linear-gradient(to right, #000, transparent)' }} />
      <div className="absolute right-0 top-0 h-full w-8 z-10 pointer-events-none"
        style={{ background: 'linear-gradient(to left, #000, transparent)' }} />

      <div
        className="flex items-center h-full whitespace-nowrap"
        style={{ animation: 'ticker-scroll 40s linear infinite' }}
      >
        {/* Render twice for seamless loop */}
        {tickerItems}
        {tickerItems}
      </div>
    </div>
  );
}
