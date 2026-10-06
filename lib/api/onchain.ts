import { ethers } from "ethers";

// USDT Contract on Ethereum Mainnet
const USDT_ADDRESS = "0xdac17f958d2ee523a2206206994597c13d831ec7";
const USDT_ABI = [
  "event Transfer(address indexed from, address indexed to, uint256 value)"
];

// Threshold to be considered a whale (e.g. 1 Million USDT = 1,000,000,000,000 due to 6 decimals)
const WHALE_THRESHOLD = 1000000;

let provider: ethers.WebSocketProvider | null = null;
let isSubscribed = false;

export function subscribeToWhales(onWhaleAlert: (alert: any) => void) {
  if (isSubscribed) return;
  isSubscribed = true;

  try {
    // Cloudflare public wss doesn't always support logs, but we'll use a public fallback.
    // In production, user should put their Infura/Alchemy key here.
    const wsUrl = process.env.NEXT_PUBLIC_ETH_WS_URL || "wss://ethereum-rpc.publicnode.com";
    provider = new ethers.WebSocketProvider(wsUrl);

    const contract = new ethers.Contract(USDT_ADDRESS, USDT_ABI, provider);

    console.log("Connected to Real Ethereum Mempool: Listening for Whales...");

    contract.on("Transfer", (from, to, value, event) => {
      // USDT has 6 decimals
      const amountFormatted = Number(ethers.formatUnits(value, 6));

      if (amountFormatted >= WHALE_THRESHOLD) {
        onWhaleAlert({
          hash: event.log.transactionHash,
          amount: amountFormatted,
          from: from,
          to: to,
          symbol: "USDT",
          timestamp: Date.now(),
        });
      }
    });

  } catch (error) {
    console.error("Failed to connect to Ethereum RPC:", error);
    isSubscribed = false;
  }
}

export function unsubscribeFromWhales() {
  if (provider) {
    provider.removeAllListeners();
    provider.destroy();
    provider = null;
    isSubscribed = false;
  }
}
