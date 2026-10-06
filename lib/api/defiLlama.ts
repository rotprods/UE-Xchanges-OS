// lib/api/defiLlama.ts
// DefiLlama API client — free, no API key required.

export interface DefiChain {
  name: string;
  tvl: number;
  change24h: number;
}

export interface DefiProtocol {
  name: string;
  tvl: number;
  category: string;
  change24h: number;
}

export interface GlobalTVL {
  tvl: number;
  change24h: number;
}

/** Fetch global DeFi TVL + 24-hour change from /v2/globalCharts */
export async function fetchGlobalTVL(): Promise<GlobalTVL> {
  const res = await fetch('https://api.llama.fi/v2/globalCharts', {
    next: { revalidate: 60 },
  });
  if (!res.ok) throw new Error(`DefiLlama globalCharts error: ${res.status}`);

  const data: Array<[number, number]> = await res.json();

  if (!Array.isArray(data) || data.length < 2) {
    return { tvl: 0, change24h: 0 };
  }

  const latest = data[data.length - 1];
  const previous = data[data.length - 2];
  const tvl = latest[1];
  const prevTvl = previous[1];
  const change24h = prevTvl > 0 ? ((tvl - prevTvl) / prevTvl) * 100 : 0;

  return { tvl, change24h };
}

/** Fetch top N chains sorted by TVL descending from /v2/chains */
export async function fetchTopChains(limit: number = 10): Promise<DefiChain[]> {
  const res = await fetch('https://api.llama.fi/v2/chains', {
    next: { revalidate: 60 },
  });
  if (!res.ok) throw new Error(`DefiLlama chains error: ${res.status}`);

  const data: Array<{
    name: string;
    tvl: number;
    change1d?: number;
    change_1d?: number;
  }> = await res.json();

  const sorted = [...data].sort((a, b) => (b.tvl ?? 0) - (a.tvl ?? 0));

  return sorted.slice(0, limit).map((chain) => ({
    name: chain.name,
    tvl: chain.tvl ?? 0,
    change24h: chain.change1d ?? chain.change_1d ?? 0,
  }));
}

/** Fetch top N protocols sorted by TVL descending from /protocols */
export async function fetchTopProtocols(limit: number = 10): Promise<DefiProtocol[]> {
  const res = await fetch('https://api.llama.fi/protocols', {
    next: { revalidate: 60 },
  });
  if (!res.ok) throw new Error(`DefiLlama protocols error: ${res.status}`);

  const data: Array<{
    name: string;
    tvl: number;
    category: string;
    change_1d?: number;
  }> = await res.json();

  const sorted = [...data].sort((a, b) => (b.tvl ?? 0) - (a.tvl ?? 0));

  return sorted.slice(0, limit).map((p) => ({
    name: p.name,
    tvl: p.tvl ?? 0,
    category: p.category ?? 'Unknown',
    change24h: p.change_1d ?? 0,
  }));
}
