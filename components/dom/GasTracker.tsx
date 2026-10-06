"use client";

import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface MempoolFee {
  fastestFee: number;
  halfHourFee: number;
  hourFee: number;
  economyFee: number;
  minimumFee: number;
}

interface RecentBlock {
  id: string;
  height: number;
  timestamp: number;
  tx_count: number;
  size: number;
  weight: number;
  medianFee: number;
}

interface GasTrackerProps {
  gasGwei: number;  // Bitcoin sat/vB from mempool worker
  txRate: number;
}

export default function GasTracker({ gasGwei, txRate }: GasTrackerProps) {
  const [fees, setFees] = useState<MempoolFee | null>(null);
  const [blocks, setBlocks] = useState<RecentBlock[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const fetchMempoolData = async () => {
      try {
        const [feesRes, blocksRes] = await Promise.all([
          fetch("https://mempool.space/api/v1/fees/recommended"),
          fetch("https://mempool.space/api/v1/blocks"),
        ]);

        if (!feesRes.ok || !blocksRes.ok) return;

        const feesData: MempoolFee = await feesRes.json();
        const blocksData: any[] = await blocksRes.json();

        if (!isMounted) return;

        setFees(feesData);
        setBlocks(
          blocksData.slice(0, 8).map((b: any) => ({
            id: b.id,
            height: b.height,
            timestamp: b.timestamp,
            tx_count: b.tx_count,
            size: b.size,
            weight: b.weight,
            medianFee: b.extras?.medianFee ?? 0,
          }))
        );
        setLoading(false);
      } catch (err) {
        // Silent fail — keep showing previous data
      }
    };

    fetchMempoolData();
    const interval = setInterval(fetchMempoolData, 15000); // Real block time ~10min, refresh every 15s
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const latestBlock = blocks[0];

  return (
    <div className="glass-panel rounded-xl p-5 w-full flex flex-col h-[340px] pointer-events-auto">
      {/* Title */}
      <div className="flex justify-between items-center mb-4 border-b border-[rgba(0,240,255,0.1)] pb-2">
        <h3 className="font-orbitron font-bold text-xs tracking-widest text-[#00F0FF]">
          BITCOIN MEMPOOL
        </h3>
        <div className="flex items-center space-x-2 font-mono text-[10px]">
          {latestBlock && (
            <>
              <span className="text-[rgba(255,255,255,0.4)]">BLOCK:</span>
              <span className="text-white">{latestBlock.height.toLocaleString()}</span>
            </>
          )}
          {loading && <span className="text-[rgba(255,255,255,0.3)]">SYNCING...</span>}
        </div>
      </div>

      {/* Fee Tiers */}
      {fees && (
        <div className="grid grid-cols-3 gap-2 mb-4">
          <div className="bg-[rgba(0,255,102,0.05)] border border-[rgba(0,255,102,0.2)] p-2 rounded-lg text-center">
            <span className="block font-mono text-[8px] text-[rgba(0,255,102,0.6)] mb-1">ECONOMY</span>
            <span className="font-orbitron text-sm font-bold text-[#00FF66]">{fees.economyFee}</span>
            <span className="block font-mono text-[8px] text-[rgba(255,255,255,0.3)]">sat/vB</span>
          </div>
          <div className="bg-[rgba(255,165,0,0.05)] border border-[rgba(255,165,0,0.2)] p-2 rounded-lg text-center">
            <span className="block font-mono text-[8px] text-[rgba(255,165,0,0.7)] mb-1">NORMAL</span>
            <span className="font-orbitron text-sm font-bold text-[#FFA500]">{fees.halfHourFee}</span>
            <span className="block font-mono text-[8px] text-[rgba(255,255,255,0.3)]">sat/vB</span>
          </div>
          <div className="bg-[rgba(255,0,85,0.05)] border border-[rgba(255,0,85,0.2)] p-2 rounded-lg text-center">
            <span className="block font-mono text-[8px] text-[rgba(255,0,85,0.7)] mb-1">PRIORITY</span>
            <span className="font-orbitron text-sm font-bold text-[#FF0055]">{fees.fastestFee}</span>
            <span className="block font-mono text-[8px] text-[rgba(255,255,255,0.3)]">sat/vB</span>
          </div>
        </div>
      )}

      {/* Recent Blocks Feed */}
      <div className="flex-1 overflow-y-auto pr-1">
        <div className="text-[9px] font-mono text-[rgba(255,255,255,0.3)] mb-2">RECENT BLOCKS</div>
        <AnimatePresence initial={false}>
          {blocks.map((block) => (
            <motion.div
              key={block.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="flex justify-between items-center border-b border-[rgba(255,255,255,0.04)] py-1.5 hover:bg-[rgba(0,240,255,0.02)] rounded"
            >
              <span className="font-orbitron text-[10px] text-[#00F0FF] font-bold">#{block.height.toLocaleString()}</span>
              <span className="font-mono text-[10px] text-[rgba(255,255,255,0.6)]">{block.tx_count} txs</span>
              <span className="font-mono text-[10px] text-[rgba(255,255,255,0.4)]">
                {(block.size / 1024).toFixed(0)} kB
              </span>
              <span className="font-mono text-[10px] text-[#FF5500]">{block.medianFee.toFixed(1)} s/vB</span>
            </motion.div>
          ))}
        </AnimatePresence>
        {loading && (
          <div className="flex items-center justify-center h-20">
            <div className="w-5 h-5 border border-t-transparent border-[#00F0FF] rounded-full animate-spin" />
          </div>
        )}
      </div>
    </div>
  );
}
