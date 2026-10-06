"use client";

import React, { useEffect, useState, useRef } from 'react';
import { useOmniStore } from '@/store/omniStore';
import { motion, AnimatePresence } from 'framer-motion';

export default function LevelUpOverlay() {
  const { playerLevel } = useOmniStore();
  const [show, setShow] = useState(false);
  const prevLevelRef = useRef(playerLevel);

  useEffect(() => {
    if (playerLevel > prevLevelRef.current) {
      setShow(true);
      const timer = setTimeout(() => setShow(false), 4000); // Hide after 4 seconds
      prevLevelRef.current = playerLevel;
      return () => clearTimeout(timer);
    }
  }, [playerLevel]);

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[9999] pointer-events-none flex items-center justify-center overflow-hidden bg-black/60 backdrop-blur-sm"
        >
          {/* Fireworks / Particles */}
          {Array.from({ length: 20 }).map((_, i) => {
            const angle = (Math.PI * 2 * i) / 20;
            const distance = 150 + Math.random() * 200;
            const x = Math.cos(angle) * distance;
            const y = Math.sin(angle) * distance;
            const color = ['#00F0FF', '#8B00FF', '#FF5500', '#FF0055', '#00FF66'][Math.floor(Math.random() * 5)];

            return (
              <motion.div
                key={i}
                initial={{ x: 0, y: 0, scale: 0, opacity: 1 }}
                animate={{ 
                  x, 
                  y, 
                  scale: [0, 1.5, 0],
                  opacity: [1, 1, 0] 
                }}
                transition={{ 
                  duration: 1.5 + Math.random() * 1,
                  ease: "easeOut",
                  times: [0, 0.7, 1]
                }}
                className="absolute w-4 h-4 rounded-full shadow-[0_0_15px_currentColor]"
                style={{ backgroundColor: color, color }}
              />
            );
          })}

          <motion.div
            initial={{ scale: 0.5, y: 50, opacity: 0 }}
            animate={{ scale: 1, y: 0, opacity: 1 }}
            exit={{ scale: 1.5, opacity: 0 }}
            transition={{ type: 'spring', bounce: 0.5, duration: 0.8 }}
            className="flex flex-col items-center justify-center text-center relative z-10"
          >
            <h1 className="text-6xl md:text-8xl font-black text-transparent bg-clip-text bg-gradient-to-b from-[#00F0FF] to-[#8B00FF] drop-shadow-[0_0_30px_rgba(0,240,255,0.8)] tracking-widest uppercase">
              Level Up!
            </h1>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="mt-4 text-3xl font-bold text-[#FF5500] drop-shadow-[0_0_10px_rgba(255,85,0,0.8)]"
            >
              You are now Level {playerLevel}
            </motion.p>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
