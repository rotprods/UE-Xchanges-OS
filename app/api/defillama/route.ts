import { NextResponse } from 'next/server';

const LLAMA_BASE = 'https://api.llama.fi';

const ENDPOINT_MAP: Record<string, string> = {
  global: '/v2/globalCharts',
  chains: '/v2/chains',
  protocols: '/protocols',
};

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const endpoint = searchParams.get('endpoint');

  if (!endpoint || !ENDPOINT_MAP[endpoint]) {
    return NextResponse.json(
      { error: `Invalid endpoint. Use one of: ${Object.keys(ENDPOINT_MAP).join(', ')}` },
      { status: 400 }
    );
  }

  const llamaUrl = `${LLAMA_BASE}${ENDPOINT_MAP[endpoint]}`;

  try {
    const res = await fetch(llamaUrl, {
      headers: { 'Accept': 'application/json' },
      next: { revalidate: 60 },
    });

    if (!res.ok) {
      throw new Error(`DefiLlama responded with status ${res.status}`);
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error: any) {
    console.error('[DefiLlama Proxy] Error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
