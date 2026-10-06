"use client";

import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Line, OrbitControls, Grid } from "@react-three/drei";
import * as THREE from "three";
import { useOmniStore } from "@/store/omniStore";

function MonteCarloScene() {
  const btcPriceStr = useOmniStore((state) => state.tickers["BTCUSDT"]?.price);
  const latestCandle = useOmniStore((state) => state.latestCandle);

  const startPrice = useMemo(() => {
    if (btcPriceStr) return parseFloat(btcPriceStr);
    if (latestCandle) return latestCandle.close;
    return 65000;
  }, [btcPriceStr, latestCandle]);

  // Generate paths
  const paths = useMemo(() => {
    const numPaths = 100;
    const steps = 50;
    const volatility = 0.02; // 2% daily simulated volatility

    const generatedPaths = [];

    for (let i = 0; i < numPaths; i++) {
      let currentPrice = startPrice;
      const points = [];

      // We center X around 0. Start at X=-25, end at X=25.
      // Spread Z to make a cone/fan effect
      const zOffset = (Math.random() - 0.5) * 20;
      
      points.push(new THREE.Vector3(-25, 0, 0));

      for (let step = 1; step <= steps; step++) {
        const u1 = Math.random();
        const u2 = Math.random();
        const z0 = Math.sqrt(-2.0 * Math.log(u1 || 0.0001)) * Math.cos(2.0 * Math.PI * u2);

        currentPrice = currentPrice * (1 + volatility * z0);

        // Scale Y relative to percentage change so it fits well visually
        // A 10% change becomes Y=10
        const y = (currentPrice / startPrice - 1) * 100;
        
        const x = (step / steps) * 50 - 25;
        const z = zOffset * (step / steps); // Spread out over time

        points.push(new THREE.Vector3(x, y, z));
      }

      generatedPaths.push({
        points,
        endPrice: currentPrice,
        isHigher: currentPrice >= startPrice,
      });
    }

    return generatedPaths;
  }, [startPrice]);

  const groupRef = useRef<THREE.Group>(null);

  useFrame(({ clock }) => {
    if (groupRef.current) {
      // Gentle rotation
      groupRef.current.rotation.y = Math.sin(clock.elapsedTime * 0.1) * 0.1;
    }
  });

  return (
    <group ref={groupRef}>
      {paths.map((path, idx) => (
        <Line
          key={idx}
          points={path.points}
          color={path.isHigher ? "#00FF66" : "#FF0055"}
          lineWidth={1.5}
          opacity={0.35}
          transparent
        />
      ))}
      <Grid
        args={[100, 100]}
        cellSize={5}
        cellThickness={1}
        cellColor="#00F0FF"
        sectionSize={25}
        sectionThickness={1.5}
        sectionColor="#8B00FF"
        fadeDistance={50}
        fadeStrength={1}
        position={[0, -20, 0]}
      />
    </group>
  );
}

export function MonteCarloPredictor() {
  return (
    <div className="w-full h-[400px] relative rounded-xl overflow-hidden border border-[rgba(0,240,255,0.1)] backdrop-blur-md" style={{ background: "rgba(10,10,20,0.6)" }}>
      <div className="absolute top-4 left-4 z-10 pointer-events-none">
        <h2 className="font-orbitron text-[#00F0FF] text-sm tracking-widest font-bold">QUANTUM PROBABILITY CONE</h2>
        <p className="font-mono text-[9px] text-white/50 mt-1 uppercase">Monte Carlo 100 Paths • 50 Steps</p>
      </div>
      <Canvas camera={{ position: [0, 10, 40], fov: 45 }}>
        <ambientLight intensity={0.5} />
        <MonteCarloScene />
        <OrbitControls enableZoom={true} enablePan={true} maxPolarAngle={Math.PI / 1.5} minPolarAngle={Math.PI / 4} />
      </Canvas>
    </div>
  );
}
