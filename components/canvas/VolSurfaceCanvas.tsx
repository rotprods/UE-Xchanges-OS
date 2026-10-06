"use client";

import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

const VolatilitySurface = () => {
  const meshRef = useRef<THREE.Mesh>(null);
  
  // We need to create a plane geometry and deform it.
  const geometry = useMemo(() => {
    const geo = new THREE.PlaneGeometry(10, 10, 50, 50);
    const posAttribute = geo.attributes.position;
    
    // Simulate implied volatility surface
    // x = strike (normalized -5 to 5)
    // y = time to expiry (normalized -5 to 5)
    // z = implied volatility
    
    for (let i = 0; i < posAttribute.count; i++) {
      const x = posAttribute.getX(i);
      const y = posAttribute.getY(i);
      
      // Volatility smile/smirk formula approximation
      // Higher IV at deep OTM (high |x|), decreases as time to expiry increases (y)
      const atmVol = 0.5;
      const skew = -0.05 * x;
      const smile = 0.05 * x * x;
      
      // y goes from -5 to 5. Let's say y = -5 is near expiry, y = 5 is far expiry.
      // We want higher vol near expiry for the smile.
      const timeToExpiry = (y + 5) / 10; // 0 to 1
      const termStructure = 0.2 * Math.exp(-timeToExpiry * 3); // decay over time
      
      const z = atmVol + skew + smile + termStructure;
      
      posAttribute.setZ(i, z * 2 - 2); // scale z for visual exaggeration, shift down
    }
    
    geo.computeVertexNormals();
    return geo;
  }, []);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.z = state.clock.elapsedTime * 0.05;
    }
  });

  return (
    <mesh ref={meshRef} geometry={geometry} rotation={[-Math.PI / 3, 0, 0]}>
      <meshBasicMaterial 
        color="#E024FF" 
        wireframe={true} 
        transparent={true} 
        opacity={0.8} 
      />
    </mesh>
  );
};

export default function VolSurfaceCanvas() {
  return (
    <div className="w-full h-full relative" style={{ minHeight: '400px' }}>
      <Canvas camera={{ position: [0, -6, 6], fov: 60 }}>
        <color attach="background" args={['transparent']} />
        <VolatilitySurface />
        <OrbitControls enableZoom={true} enablePan={true} autoRotate autoRotateSpeed={0.5} />
      </Canvas>
    </div>
  );
}
