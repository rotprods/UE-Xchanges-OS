import React, { useRef, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

interface HologramGlobeProps {
  txRate: number;
  pulseTrigger: number;
}

export default function HologramGlobe({ txRate, pulseTrigger }: HologramGlobeProps) {
  const pointsRef = useRef<THREE.Points>(null);
  const materialRef = useRef<THREE.PointsMaterial>(null);
  const glowRef = useRef<THREE.Mesh>(null);

  // Generate 8000 particles on a Fibonacci Sphere
  const particleCount = 8000;
  const [positions, initialScales, initialPositions] = useMemo(() => {
    const pos = new Float32Array(particleCount * 3);
    const scales = new Float32Array(particleCount);
    const initialPos = [];

    const goldenRatio = (1 + Math.sqrt(5)) / 2;
    const angleIncrement = 2 * Math.PI * goldenRatio;

    for (let i = 0; i < particleCount; i++) {
      // Fibonacci sphere coordinates
      const t = i / particleCount;
      const inclination = Math.acos(1 - 2 * t);
      const azimuth = angleIncrement * i;

      const r = 2.0; // Globe Radius
      const x = r * Math.sin(inclination) * Math.cos(azimuth);
      const y = r * Math.sin(inclination) * Math.sin(azimuth);
      const z = r * Math.cos(inclination);

      pos[i * 3] = x;
      pos[i * 3 + 1] = y;
      pos[i * 3 + 2] = z;

      initialPos.push(new THREE.Vector3(x, y, z));
      
      // Randomize initial particle scales
      scales[i] = Math.random() * 0.5 + 0.5;
    }

    return [pos, scales, initialPos];
  }, [particleCount]);

  // Keep track of transaction spikes and trigger local particle excitation
  const excitationState = useRef({
    intensity: 0.0,
    pulseSpeed: 1.0,
  });

  // Handle pulse trigger changes
  React.useEffect(() => {
    if (pulseTrigger > 0) {
      excitationState.current.intensity = 1.0;
    }
  }, [pulseTrigger]);

  useFrame((state) => {
    const time = state.clock.getElapsedTime();

    // Rotate points
    if (pointsRef.current) {
      // Rotation speed increases with transaction rate
      const baseRotationSpeed = 0.05;
      const bonusRotation = Math.min(0.2, txRate * 0.005);
      pointsRef.current.rotation.y = time * (baseRotationSpeed + bonusRotation);
      pointsRef.current.rotation.x = Math.sin(time * 0.1) * 0.1;
    }

    // Rotate halo mesh
    if (glowRef.current) {
      glowRef.current.rotation.y = -time * 0.02;
      
      // Pulse scale based on global transaction spike intensity
      const pulseScale = 1.0 + Math.sin(time * 6.0) * 0.01 + excitationState.current.intensity * 0.08;
      glowRef.current.scale.set(pulseScale, pulseScale, pulseScale);
    }

    // Decay the transaction spike excitation
    if (excitationState.current.intensity > 0) {
      excitationState.current.intensity -= 0.05; // Decay rate
      if (excitationState.current.intensity < 0) {
        excitationState.current.intensity = 0;
      }
    }

    // Deform points dynamically using raw position buffer
    if (pointsRef.current) {
      const geometry = pointsRef.current.geometry;
      const positionsAttr = geometry.attributes.position;
      
      if (positionsAttr) {
        const array = positionsAttr.array as Float32Array;
        
        for (let i = 0; i < particleCount; i++) {
          const initVec = initialPositions[i];
          
          // Noise factor
          const wave = Math.sin(time * 1.5 + initVec.y * 2.0 + initVec.x * 2.0) * 0.03;
          // React factor (excite particles when transaction intensity is high)
          const excite = excitationState.current.intensity * (Math.random() - 0.5) * 0.15;
          
          const multiplier = 1.0 + wave + excite;
          
          array[i * 3] = initVec.x * multiplier;
          array[i * 3 + 1] = initVec.y * multiplier;
          array[i * 3 + 2] = initVec.z * multiplier;
        }
        
        positionsAttr.needsUpdate = true;
      }
    }

    // Pulse colors in material
    if (materialRef.current) {
      // Interpolate from deep cyan to neon orange on transaction ticks
      const colorCyan = new THREE.Color("#00F0FF");
      const colorOrange = new THREE.Color("#FF5500");
      const mixedColor = colorCyan.clone().lerp(colorOrange, excitationState.current.intensity);
      materialRef.current.color.copy(mixedColor);
    }
  });

  return (
    <group>
      {/* 3D Wireframe inner sphere to represent digital layout */}
      <mesh ref={glowRef}>
        <sphereGeometry args={[1.98, 24, 24]} />
        <meshBasicMaterial
          color="#8B00FF"
          wireframe
          transparent
          opacity={0.06}
          blending={THREE.AdditiveBlending}
        />
      </mesh>

      {/* Hologram Particle Points */}
      <points ref={pointsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            args={[positions, 3]}
          />
        </bufferGeometry>
        <pointsMaterial
          ref={materialRef}
          size={0.025}
          color="#00F0FF"
          transparent
          opacity={0.7}
          sizeAttenuation={true}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </points>

      {/* Ambient particles surrounding the globe */}
      <points>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            args={[
              useMemo(() => {
                const arr = new Float32Array(600 * 3);
                for (let i = 0; i < 600; i++) {
                  const theta = Math.random() * Math.PI * 2;
                  const phi = Math.acos(Math.random() * 2 - 1);
                  const r = 3.5 + Math.random() * 3.0; // Distant particles
                  arr[i * 3] = r * Math.sin(phi) * Math.cos(theta);
                  arr[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
                  arr[i * 3 + 2] = r * Math.cos(phi);
                }
                return arr;
              }, []),
              3,
            ]}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.015}
          color="#8B00FF"
          transparent
          opacity={0.3}
          sizeAttenuation={true}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </points>
    </group>
  );
}
