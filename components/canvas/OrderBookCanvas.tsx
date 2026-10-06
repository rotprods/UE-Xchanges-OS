"use client";

import React from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Environment } from "@react-three/drei";
import OrderBookTerrain from "./OrderBookTerrain";

export default function OrderBookCanvas() {
  return (
    <div className="w-full h-full absolute inset-0">
      <Canvas camera={{ position: [0, 5, 15], fov: 45 }}>
        <color attach="background" args={["#0a0510"]} />
        <ambientLight intensity={0.5} />
        <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} intensity={1} />
        
        <OrderBookTerrain />
        
        <OrbitControls 
          enableZoom={false} 
          enablePan={false}
          autoRotate={true}
          autoRotateSpeed={0.5}
          maxPolarAngle={Math.PI / 2.2} // Prevent looking from bottom
        />
        <Environment preset="night" />
      </Canvas>
    </div>
  );
}
