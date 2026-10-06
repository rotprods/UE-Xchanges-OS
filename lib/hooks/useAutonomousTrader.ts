/**
 * useAutonomousTrader — React hook that bridges the AutonomousOrchestrator
 * with the Zustand omniStore, feeding live market data to the graph engine.
 * 
 * Usage: Place in AppShell or any top-level component.
 * When enabled, it:
 * 1. Subscribes to omniStore tickers/indicators
 * 2. Feeds data to the orchestrator every second
 * 3. Exposes orchestrator state to the UI
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { useOmniStore } from "../../store/omniStore";
import {
  getOrchestrator,
  type OrchestratorState,
  type OrchestratorConfig,
} from "../orchestrator/AutonomousOrchestrator";

export function useAutonomousTrader() {
  const orchestrator = useRef(getOrchestrator());
  const [orchState, setOrchState] = useState<OrchestratorState>(
    orchestrator.current.getState()
  );
  const feedIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Subscribe to state changes from orchestrator
  useEffect(() => {
    orchestrator.current.setOnStateChange((state) => {
      setOrchState(state);
    });

    return () => {
      orchestrator.current.setOnStateChange(() => {});
    };
  }, []);

  // Feed market data from store to orchestrator
  useEffect(() => {
    feedIntervalRef.current = setInterval(() => {
      const store = useOmniStore.getState();
      const tickers = store.tickers;

      // Extract prices for the orchestrator
      const prices: Record<string, number> = {};
      for (const [sym, ticker] of Object.entries(tickers)) {
        prices[sym] = parseFloat(ticker.price);
      }
      orchestrator.current.setCurrentPrices(prices);

      // Feed all available data
      orchestrator.current.feedMarketData({
        tickers,
        // These will be populated when indicators are computed
        // For now, the orchestrator handles missing data gracefully
      });
    }, 1000);

    return () => {
      if (feedIntervalRef.current) clearInterval(feedIntervalRef.current);
    };
  }, []);

  const start = useCallback(() => {
    orchestrator.current.start();
  }, []);

  const stop = useCallback(() => {
    orchestrator.current.stop();
  }, []);

  const updateConfig = useCallback((update: Partial<OrchestratorConfig>) => {
    orchestrator.current.updateConfig(update);
  }, []);

  return {
    state: orchState,
    config: orchestrator.current.getConfig(),
    start,
    stop,
    updateConfig,
    isRunning: orchState.isRunning,
    currentSignal: orchState.currentSignal,
    wallets: orchState.wallets,
    logs: orchState.logs,
    evaluationCount: orchState.evaluationCount,
  };
}
