/**
 * Supabase Client — Handles all database operations for Chronos Quantum.
 * 
 * Falls back gracefully when NEXT_PUBLIC_SUPABASE_URL is not configured.
 * All functions return null/empty arrays when Supabase is unavailable.
 */

import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

export const supabase: SupabaseClient | null =
  supabaseUrl && supabaseAnonKey
    ? createClient(supabaseUrl, supabaseAnonKey)
    : null;

// ─── Market Snapshots ─────────────────────────────────────────────────────────

export async function insertSnapshot(data: Record<string, any>) {
  if (!supabase) return null;
  const { error } = await supabase.from("market_snapshots").insert(data);
  if (error) console.warn("[supabase] insertSnapshot error:", error.message);
  return !error;
}

export async function getSnapshots(symbol: string, limit = 100) {
  if (!supabase) return [];
  const { data } = await supabase
    .from("market_snapshots")
    .select("*")
    .eq("symbol", symbol)
    .order("timestamp", { ascending: false })
    .limit(limit);
  return data || [];
}

export async function getLatestSnapshot(symbol: string) {
  if (!supabase) return null;
  const { data } = await supabase
    .from("market_snapshots")
    .select("*")
    .eq("symbol", symbol)
    .order("timestamp", { ascending: false })
    .limit(1);
  return data?.[0] || null;
}

// ─── AI Decisions ─────────────────────────────────────────────────────────────

export async function insertDecision(data: Record<string, any>) {
  if (!supabase) return null;
  const { error } = await supabase.from("ai_decisions").insert(data);
  if (error) console.warn("[supabase] insertDecision error:", error.message);
  return !error;
}

export async function getDecisions(walletId: string, limit = 50) {
  if (!supabase) return [];
  const { data } = await supabase
    .from("ai_decisions")
    .select("*")
    .eq("wallet_id", walletId)
    .order("timestamp", { ascending: false })
    .limit(limit);
  return data || [];
}

// ─── Trades ───────────────────────────────────────────────────────────────────

export async function insertTrade(data: Record<string, any>) {
  if (!supabase) return null;
  const { error } = await supabase.from("trades").insert(data);
  if (error) console.warn("[supabase] insertTrade error:", error.message);
  return !error;
}

export async function getTrades(walletId: string, limit = 100) {
  if (!supabase) return [];
  const { data } = await supabase
    .from("trades")
    .select("*")
    .eq("wallet_id", walletId)
    .order("timestamp", { ascending: false })
    .limit(limit);
  return data || [];
}

// ─── Paper Wallets ────────────────────────────────────────────────────────────

export async function upsertWallet(walletData: Record<string, any>) {
  if (!supabase) return null;
  const { error } = await supabase
    .from("paper_wallets")
    .upsert(walletData, { onConflict: "id" });
  if (error) console.warn("[supabase] upsertWallet error:", error.message);
  return !error;
}

export async function getWallets() {
  if (!supabase) return [];
  const { data } = await supabase
    .from("paper_wallets")
    .select("*")
    .order("total_return", { ascending: false });
  return data || [];
}

// ─── Training Episodes ───────────────────────────────────────────────────────

export async function insertTrainingEpisode(data: Record<string, any>) {
  if (!supabase) return null;
  const { error } = await supabase.from("training_episodes").insert(data);
  if (error) console.warn("[supabase] insertTrainingEpisode:", error.message);
  return !error;
}

export async function getTrainingEpisodes(walletId: string, limit = 20) {
  if (!supabase) return [];
  const { data } = await supabase
    .from("training_episodes")
    .select("*")
    .eq("wallet_id", walletId)
    .order("end_ts", { ascending: false })
    .limit(limit);
  return data || [];
}

// ─── Signal History ──────────────────────────────────────────────────────────

export async function insertSignalHistory(records: Record<string, any>[]) {
  if (!supabase) return null;
  const { error } = await supabase.from("signal_history").insert(records);
  if (error) console.warn("[supabase] insertSignalHistory:", error.message);
  return !error;
}

export async function getSignalHistory(symbol: string, nodeId: string, limit = 200) {
  if (!supabase) return [];
  const { data } = await supabase
    .from("signal_history")
    .select("*")
    .eq("symbol", symbol)
    .eq("node_id", nodeId)
    .order("timestamp", { ascending: false })
    .limit(limit);
  return data || [];
}

// ─── Strategies ──────────────────────────────────────────────────────────────

export async function upsertStrategy(data: Record<string, any>) {
  if (!supabase) return null;
  const { error } = await supabase
    .from("strategies")
    .upsert(data, { onConflict: "id" });
  if (error) console.warn("[supabase] upsertStrategy:", error.message);
  return !error;
}

export async function getStrategies() {
  if (!supabase) return [];
  const { data } = await supabase.from("strategies").select("*");
  return data || [];
}

// ─── Utility ─────────────────────────────────────────────────────────────────

export function isSupabaseConfigured(): boolean {
  return supabase !== null;
}
