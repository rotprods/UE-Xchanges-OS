import React from "react";
import { Canvas } from "@react-three/fiber";
import HologramGlobe from "./HologramGlobe";
import PostFX from "./PostFX";

interface QuantumCanvasProps {
  txRate: number;
  pulseTrigger: number;
}

export default function QuantumCanvas({ txRate, pulseTrigger }: QuantumCanvasProps) {
  // Let the PostFX intensity decay or pulse based on pulseTrigger
  const [effectIntensity, setEffectIntensity] = React.useState(0);

  React.useEffect(() => {
    if (pulseTrigger > 0) {
      setEffectIntensity(1.0);
    }
  }, [pulseTrigger]);

  React.useEffect(() => {
    if (effectIntensity > 0) {
      const interval = setInterval(() => {
        setEffectIntensity((prev) => {
          const next = prev - 0.05;
          if (next <= 0) {
            clearInterval(interval);
            return 0;
          }
          return next;
        });
      }, 30);
      return () => clearInterval(interval);
    }
  }, [effectIntensity]);

  return (
    <div className="w-full h-full">
      <Canvas
        camera={{ position: [0, 0, 4.8], fov: 60 }}
        gl={{ alpha: true, antialias: false }}
        style={{ pointerEvents: "none" }}
      >
        <ambientLight intensity={0.4} />
        <pointLight position={[10, 10, 10]} intensity={1.5} color="#00F0FF" />
        
        {/* Globe Scene */}
        <HologramGlobe txRate={txRate} pulseTrigger={pulseTrigger} />
        
        {/* Visual FX filters */}
        <React.Suspense fallback={null}>
          <PostFX intensity={effectIntensity} />
        </React.Suspense>
      </Canvas>
    </div>
  );
}
