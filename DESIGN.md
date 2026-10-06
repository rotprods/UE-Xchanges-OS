---
colors:
  primary: "#00F0FF"       # Electric Cyan
  secondary: "#8B00FF"     # Plasma Purple
  accent: "#FF5500"        # Quantum Orange
  bg: "#05050A"            # Deep Cyber Black
  cardBg: "rgba(10, 10, 20, 0.6)" # Glassmorphic Navy
  border: "rgba(0, 240, 255, 0.15)" # Subtle Cyan border
  success: "#00FF66"       # Neon Green
typography:
  heading: "Orbitron"
  body: "Inter"
  mono: "JetBrains Mono"
spacing:
  base: 8px
  radius: 12px
---

# DESIGN.md — Chronos Quantum DeFi Dashboard

Design DNA for the high-fidelity Chronos Quantum Holographic Command Center.

## Color Palette & Theme
All layers must respect the primary dark cyberpunk theme:
- `primary`: `#00F0FF` used for critical interface indicators, holographic nodes, and high-priority metrics.
- `secondary`: `#8B00FF` used for particle glow backdrops, radial gradients, and secondary accents.
- `accent`: `#FF5500` reserved for high-velocity transaction spikes, critical alerts, and active trading triggers.
- `bg`: `#05050A` is the absolute background for the fixed Canvas container.
- `cardBg`: `rgba(10, 10, 20, 0.6)` with `backdrop-filter: blur(12px)` for a glassmorphic dashboard HUD floating above the 3D scene.

## Typography
- **Headings**: `Orbitron` from Google Fonts. Used for metrics, terminal indicators, and screen headers.
- **Body & Labels**: `Inter` from Google Fonts. Used for general reading and static label details.
- **Numbers & Logs**: `JetBrains Mono`. Used for prices, gas rates, transaction hashes, and live tickers.

## Spacing & Borders
- Spacing follows a strict `8px` grid (`base: 8px`).
- Border Radius should be a consistent `12px` (`radius: 12px`) for all floating cards and panels.
- Cards must use a subtle glow border: `border: 1px solid rgba(0, 240, 255, 0.15)` combined with `box-shadow: 0 0 15px rgba(0, 240, 255, 0.05)`.
