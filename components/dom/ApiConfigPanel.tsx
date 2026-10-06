'use client';

import { useState, useEffect } from 'react';
import { useOmniStore } from '@/store/omniStore';

export default function ApiConfigPanel() {
  const { apiKeys, setApiKeys, realModeEnabled, toggleRealMode } = useOmniStore();
  const [apiKey, setApiKey] = useState('');
  const [secret, setSecret] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    // Load from local storage on mount if available
    const stored = localStorage.getItem('binance_api_keys');
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        if (parsed.binanceApiKey && parsed.binanceSecret) {
          setApiKeys(parsed);
          setApiKey(parsed.binanceApiKey);
          setSecret(parsed.binanceSecret);
        }
      } catch (e) {
        console.error('Failed to parse stored API keys', e);
      }
    } else {
      setApiKey(apiKeys.binanceApiKey);
      setSecret(apiKeys.binanceSecret);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSave = () => {
    setApiKeys({ binanceApiKey: apiKey, binanceSecret: secret });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="bg-black/40 border border-white/10 rounded-xl p-6 backdrop-blur-md text-white max-w-md w-full">
      <h2 className="text-xl font-bold mb-4 font-mono text-cyan-400">EXCHANGE EXECUTION</h2>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm text-gray-400 mb-1">Binance API Key (Testnet)</label>
          <input 
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            className="w-full bg-black/50 border border-white/20 rounded p-2 text-white focus:outline-none focus:border-cyan-400 font-mono text-sm"
            placeholder="Enter API Key"
          />
        </div>
        
        <div>
          <label className="block text-sm text-gray-400 mb-1">Binance API Secret (Testnet)</label>
          <input 
            type="password"
            value={secret}
            onChange={(e) => setSecret(e.target.value)}
            className="w-full bg-black/50 border border-white/20 rounded p-2 text-white focus:outline-none focus:border-cyan-400 font-mono text-sm"
            placeholder="Enter API Secret"
          />
        </div>

        <button 
          onClick={handleSave}
          className="w-full py-2 bg-cyan-500/20 hover:bg-cyan-500/40 border border-cyan-500/50 rounded text-cyan-400 font-mono uppercase transition-colors"
        >
          {saved ? 'Saved!' : 'Save Keys'}
        </button>

        <div className="mt-6 pt-4 border-t border-white/10 flex items-center justify-between">
          <div>
            <div className="font-mono text-sm">REAL EXECUTION MODE</div>
            <div className="text-xs text-gray-400">Execute real trades via CCXT</div>
          </div>
          <button 
            onClick={toggleRealMode}
            className={`w-12 h-6 rounded-full relative transition-colors ${realModeEnabled ? 'bg-red-500' : 'bg-gray-700'}`}
          >
            <div className={`w-4 h-4 rounded-full bg-white absolute top-1 transition-transform ${realModeEnabled ? 'left-7' : 'left-1'}`} />
          </button>
        </div>
        {realModeEnabled && (
          <div className="text-xs text-red-400 mt-2 p-2 bg-red-500/10 border border-red-500/20 rounded">
            WARNING: Real execution mode is active. Trades will be sent to Binance Testnet.
          </div>
        )}
      </div>
    </div>
  );
}
