import { neon } from "@neondatabase/serverless";
import { drizzle } from "drizzle-orm/neon-http";
import * as schema from "./schema";

const databaseUrl = process.env.DATABASE_URL;

/**
 * Database singleton — returns null when DATABASE_URL is not configured,
 * allowing the app to run without a DB connection (in-memory fallback).
 */
function createDb() {
  if (!databaseUrl) {
    console.warn(
      "[db] DATABASE_URL is not set — running without database connection"
    );
    return null;
  }

  const sql = neon(databaseUrl);
  return drizzle(sql, { schema });
}

export const db = createDb();
export type Database = NonNullable<ReturnType<typeof createDb>>;

// ─── Supabase (preferred) ────────────────────────────────────────────────────
export {
  supabase,
  isSupabaseConfigured,
  insertSnapshot,
  insertDecision,
  insertTrade,
  getSnapshots,
  getDecisions,
  upsertWallet,
  getWallets,
  insertTrainingEpisode,
  insertSignalHistory,
  getLatestSnapshot,
  getTrades,
  getTrainingEpisodes,
  getSignalHistory,
  upsertStrategy,
  getStrategies,
} from "./supabase";
