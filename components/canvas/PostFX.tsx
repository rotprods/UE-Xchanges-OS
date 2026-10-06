import React, { useRef } from "react";
import { EffectComposer, Bloom, ChromaticAberration, Glitch, Noise } from "@react-three/postprocessing";
import { GlitchMode } from "postprocessing";
import * as THREE from "three";
import { useFrame } from "@react-three/fiber";
import { useOmniStore } from "../../store/omniStore";

interface PostFXProps {
  intensity: number;
}

export default function PostFX({ intensity }: PostFXProps) {
  const panicLevel = useOmniStore((state) => state.panicLevel);
  const decayPanic = useOmniStore((state) => state.decayPanic);

  // Decay panic smoothly over frames
  useFrame(() => {
    if (panicLevel > 0) {
      decayPanic();
    }
  });

  const baseOffset = 0.0015 + intensity * 0.004;
  const panicOffset = panicLevel * 0.05;
  const totalOffset = baseOffset + panicOffset;

  return (
    <EffectComposer>
      {/* Bloom glow for futuristic glowy vector aesthetic */}
      <Bloom
        intensity={1.2 + intensity * 1.5 + panicLevel * 3}
        luminanceThreshold={0.15 - panicLevel * 0.1}
        luminanceSmoothing={0.9}
        mipmapBlur
      />
      {/* Chromatic aberration shifts electric cyan and plasma purple on corners */}
      <ChromaticAberration
        offset={new THREE.Vector2(totalOffset, totalOffset)}
        radialModulation={true}
        modulationOffset={0.2}
      />
      <Glitch
        delay={new THREE.Vector2(0.1, 0.3)}
        duration={new THREE.Vector2(0.1, 0.4)}
        strength={new THREE.Vector2(0.3 * panicLevel, 1.0 * panicLevel)}
        mode={GlitchMode.SPORADIC}
        active={panicLevel > 0.1}
        ratio={0.85}
      />
      <Noise opacity={panicLevel > 0.5 ? panicLevel * 0.3 : 0} />
    </EffectComposer>
  );
}
