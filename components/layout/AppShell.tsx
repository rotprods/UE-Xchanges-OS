"use client";

import React, { useEffect, useRef } from "react";
import * as Comlink from "comlink";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import AiCopilot from "../dom/AiCopilot";
import { VoiceCopilot } from "../dom/VoiceCopilot";
import PanicButton from "../dom/PanicButton";
import { useOmniStore } from "../../store/omniStore";
import { audioController } from "../../utils/audioController";
import { subscribeToWhales, unsubscribeFromWhales } from "../../lib/api/onchain";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const workerRef = useRef<any>(null);
  const prevVolume = useRef(0);
  
  const setTickers = useOmniStore((state) => state.setTickers);
  const setStats = useOmniStore((state) => state.setStats);
  const incrementPulse = useOmniStore((state) => state.incrementPulse);
  const chartSymbol = useOmniStore((state) => state.chartSymbol);
  const chartInterval = useOmniStore((state) => state.chartInterval);
  const marketMode = useOmniStore((state) => state.marketMode);
  const setDefiTVL = useOmniStore((state) => state.setDefiTVL);
  const setNewsItems = useOmniStore((state) => state.setNewsItems);

  // Initialize Web Worker globally — persists across all pages
  useEffect(() => {
    const worker = new Worker(
      new URL("../../workers/ticker.worker.ts", import.meta.url),
      { type: "module" }
    );
    const TickerWorkerClass: any = Comlink.wrap(worker);

    const initWorker = async () => {
      try {
        const instance = await new TickerWorkerClass();
        workerRef.current = instance;

        await instance.registerCallback(
          Comlink.proxy((data: any) => {
            const store = useOmniStore.getState();
            if (data.mempoolEvent) {
              store.addMempoolEvent(data.mempoolEvent);
              if (store.audioEnabled) audioController.playTick(1200, 0.02, 0.01);
              if (data.mempoolEvent.gas > 100) {
                store.addToast("NETWORK SPIKE", `High Gas: ${data.mempoolEvent.gas} Gwei on ${data.mempoolEvent.network}`, "network");
              }
            }
            if (data.orderBook) store.setOrderBook(data.orderBook);
            if (data.whaleAlert) {
              store.addWhaleAlert(data.whaleAlert);
              if (store.audioEnabled) audioController.playWhaleSonarPing();
              store.addToast("WHALE DETECTED", `Transfer: ${data.whaleAlert.amountUsd} in ${data.whaleAlert.token}`, "whale");
            }
            if (data.rektAlert) {
              store.addToast(`LIQUIDATION (${data.rektAlert.side})`, data.rektAlert.message, "rekt");
              store.triggerPanic();
              if (store.audioEnabled) audioController.playTick(100, 0.5, 0.05);
            }
            if (data.latestCandle) {
              store.setLatestCandle(data.latestCandle);
            }
            if (data.tickers) store.setTickers(data.tickers);
            if (data.stats) {
              store.setStats(data.stats);
              if (data.stats.totalVolume24h > prevVolume.current) {
                const diff = data.stats.totalVolume24h - prevVolume.current;
                if (diff > 500000) {
                  store.incrementPulse();
                }
                prevVolume.current = data.stats.totalVolume24h;
              }
            }
            if (data.defiData) store.setDefiTVL(data.defiData);
            if (data.newsData) store.setNewsItems(data.newsData);
          })
        );

        await instance.start();
        const store = useOmniStore.getState();
        await instance.setKlineConfig(store.chartSymbol, store.chartInterval);
      } catch (err) {
        console.error("Failed to run Web Worker setup:", err);
      }
    };

    initWorker();

    return () => {
      if (workerRef.current) workerRef.current.stop();
      worker.terminate();
    };
  }, []);

  // Sync kline config changes to worker
  useEffect(() => {
    if (workerRef.current) {
      workerRef.current.setKlineConfig(chartSymbol, chartInterval);
    }
  }, [chartSymbol, chartInterval]);

  // Sync market mode changes to worker
  useEffect(() => {
    if (workerRef.current) {
      workerRef.current.setMarketMode(marketMode);
    }
  }, [marketMode]);

  useEffect(() => {
    // Start listening to the real Ethereum blockchain
    subscribeToWhales((alert) => {
      useOmniStore.getState().addMempoolEvent({
        hash: alert.hash,
        network: "ETH",
        gas: 15,
        value: `${alert.amount} USDT`,
        time: alert.timestamp
      });
      // Optionally notify the UI toast
    });

    return () => {
      unsubscribeFromWhales();
    };
  }, []);

  return (
    <div className="min-h-screen bg-[#05050A] text-white">
      <Sidebar />
      <div className="ml-16">
        <TopBar />
        <main className="relative">
          {children}
        </main>
      </div>
      <AiCopilot />
      <VoiceCopilot />
      <PanicButton />
    </div>
  );
}
