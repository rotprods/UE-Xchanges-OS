import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Keep ccxt and ethers server-side only (they are Node.js packages)
  serverExternalPackages: ["ccxt", "ethers"],

  // Security headers
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(self), geolocation=()",
          },
        ],
      },
    ];
  },

  // Optimize remote images (news feed thumbnails)
  images: {
    remotePatterns: [
      { hostname: "images.cryptocompare.com" },
      { hostname: "resources.cryptocompare.com" },
    ],
  },
};

export default nextConfig;
