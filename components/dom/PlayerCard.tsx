"use client";

import React, { useMemo } from 'react';
import { useOmniStore } from '@/store/omniStore';

export default function PlayerCard() {
  const { playerLevel, playerExp, currentTheme, setTheme } = useOmniStore();

  const expRequired = playerLevel * 1000;
  const prevExpRequired = playerLevel > 1 ? (playerLevel - 1) * 1000 : 0;
  const currentLevelExp = playerExp; // Actually wait, if playerExp is cumulative, progress is (playerExp - prevExpRequired) / (expRequired - prevExpRequired). But if it doesn't subtract, the formula is:
  // Since `playerExp` just accumulates, and next level is when `newExp >= newLevel * 1000`, wait! 
  // Level 1 -> 1000 required for Level 2.
  // Level 2 -> 2000 required for Level 3.
  // If playerExp = 1500, they are Level 2. Progress to Level 3 is 1500 / 2000? No, progress inside Level 2 is from 1000 to 2000.
  // So currentLevelProgress = (1500 - 1000) / (2000 - 1000) = 50%.
  
  const expNeededForCurrentLevel = (playerLevel - 1) * 1000;
  const expNeededForNextLevel = playerLevel * 1000;
  
  const progressPercent = Math.min(100, Math.max(0, ((playerExp - expNeededForCurrentLevel) / (expNeededForNextLevel - expNeededForCurrentLevel)) * 100));

  const availableThemes = [
    { id: 'cyberpunk', name: 'Cyberpunk (Default)', level: 1, color: '#00F0FF' },
    { id: 'bloodmoon', name: 'Blood Moon', level: 5, color: '#FF0055' },
    { id: 'matrix', name: 'Matrix Green', level: 10, color: '#00FF66' },
    { id: 'synthwave', name: 'Synthwave', level: 20, color: '#8B00FF' },
  ];

  return (
    <div className="p-4 rounded-xl bg-[#0a0a1499] backdrop-blur-md border border-[#00F0FF1a] flex flex-col gap-4 text-white">
      <div className="flex items-center gap-4">
        {/* Avatar Placeholder */}
        <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-[#00F0FF] to-[#8B00FF] flex items-center justify-center border-2 border-[#00F0FF] shadow-[0_0_15px_rgba(0,240,255,0.5)]">
          <span className="text-xl font-bold">OP</span>
        </div>
        
        <div className="flex-1">
          <div className="flex justify-between items-end mb-1">
            <h2 className="text-xl font-bold text-[#00F0FF] drop-shadow-[0_0_8px_rgba(0,240,255,0.8)]">Omni Player</h2>
            <span className="text-sm font-semibold text-[#FF5500]">Level {playerLevel}</span>
          </div>
          
          {/* EXP Bar */}
          <div className="relative w-full h-3 bg-black rounded-full overflow-hidden border border-[#00F0FF33]">
            <div 
              className="absolute top-0 left-0 h-full bg-gradient-to-r from-[#00F0FF] to-[#00FF66] transition-all duration-500 ease-out shadow-[0_0_10px_rgba(0,255,102,0.8)]"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <div className="text-right text-xs mt-1 text-gray-400">
            {Math.floor(playerExp)} / {expNeededForNextLevel} EXP
          </div>
        </div>
      </div>

      <div className="mt-2">
        <h3 className="text-sm font-semibold mb-2 text-gray-300">Unlockable Themes</h3>
        <div className="grid grid-cols-2 gap-2">
          {availableThemes.map((theme) => {
            const isUnlocked = playerLevel >= theme.level;
            const isActive = currentTheme === theme.id;
            
            return (
              <button
                key={theme.id}
                disabled={!isUnlocked}
                onClick={() => setTheme(theme.id)}
                className={`p-2 rounded text-xs text-left border transition-all ${
                  isActive 
                    ? 'border-[#00F0FF] bg-[#00F0FF1a] shadow-[0_0_10px_rgba(0,240,255,0.2)]' 
                    : isUnlocked 
                      ? 'border-gray-600 hover:border-gray-400' 
                      : 'border-gray-800 opacity-50 cursor-not-allowed'
                }`}
              >
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: theme.color }} />
                  <span className={isActive ? 'text-white' : 'text-gray-400'}>{theme.name}</span>
                </div>
                {!isUnlocked && (
                  <div className="mt-1 text-[10px] text-[#FF0055]">Unlocks at Lvl {theme.level}</div>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
