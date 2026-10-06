/**
 * DataCache — In-memory TTL cache to reduce API calls and improve latency.
 *
 * Different cache instances with different TTLs for different data categories.
 */

interface CacheEntry<T> {
  data: T;
  expiresAt: number;
}

export class DataCache {
  private store: Map<string, CacheEntry<any>> = new Map();
  private defaultTTL: number;

  constructor(defaultTTLMs: number = 60000) {
    this.defaultTTL = defaultTTLMs;
  }

  get<T>(key: string): T | null {
    const entry = this.store.get(key);
    if (!entry) return null;
    if (Date.now() > entry.expiresAt) {
      this.store.delete(key);
      return null;
    }
    return entry.data as T;
  }

  set<T>(key: string, data: T, ttlMs?: number): void {
    this.store.set(key, {
      data,
      expiresAt: Date.now() + (ttlMs || this.defaultTTL),
    });
  }

  has(key: string): boolean {
    return this.get(key) !== null;
  }

  delete(key: string): void {
    this.store.delete(key);
  }

  clear(): void {
    this.store.clear();
  }

  size(): number {
    const now = Date.now();
    for (const [key, entry] of this.store) {
      if (now > entry.expiresAt) this.store.delete(key);
    }
    return this.store.size;
  }

  /**
   * Get cached value or fetch, cache, and return.
   */
  async getOrFetch<T>(
    key: string,
    fetcher: () => Promise<T>,
    ttlMs?: number
  ): Promise<T> {
    const cached = this.get<T>(key);
    if (cached !== null) return cached;
    const data = await fetcher();
    this.set(key, data, ttlMs);
    return data;
  }

  /**
   * Get stats for debugging.
   */
  getStats(): { size: number; keys: string[] } {
    this.size(); // clean expired
    return {
      size: this.store.size,
      keys: Array.from(this.store.keys()),
    };
  }
}

// ─── Singleton caches with different TTLs ─────────────────────────────────────

/** 5 seconds — for live prices */
export const priceCache = new DataCache(5_000);

/** 1 minute — for computed indicators */
export const indicatorCache = new DataCache(60_000);

/** 30 seconds — for on-chain data (mempool, whales) */
export const onchainCache = new DataCache(30_000);

/** 5 minutes — for sentiment data (Fear & Greed) */
export const sentimentCache = new DataCache(300_000);

/** 15 minutes — for macro data (DeFi TVL, dominance) */
export const macroCache = new DataCache(900_000);

/** 5 minutes — for full snapshots */
export const snapshotCache = new DataCache(300_000);
