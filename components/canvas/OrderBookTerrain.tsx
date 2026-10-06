import React, { useRef, useMemo, useEffect } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { useOmniStore } from "../../store/omniStore";

const OrderBookTerrain = () => {
  // Use Zustand hook directly so React-Three-Fiber receives updates
  const orderBook = useOmniStore((state) => state.orderBook);
  
  const meshRef = useRef<THREE.InstancedMesh>(null);
  const particlesRef = useRef<THREE.InstancedMesh>(null);
  
  // Total instances: 20 bids + 20 asks
  const totalCount = 40;
  const particleCount = 100;
  
  const dummy = useMemo(() => new THREE.Object3D(), []);
  const particleDummy = useMemo(() => new THREE.Object3D(), []);
  
  // Particle physics data
  const particlesData = useMemo(() => {
    const data = [];
    for (let i = 0; i < particleCount; i++) {
      data.push({
        position: new THREE.Vector3((Math.random() - 0.5) * 10, -2, (Math.random() - 0.5) * 5),
        velocity: new THREE.Vector3(0, 0, 0),
        rotation: new THREE.Vector3(Math.random() * Math.PI, Math.random() * Math.PI, 0),
        rotationSpeed: new THREE.Vector3((Math.random() - 0.5) * 0.2, (Math.random() - 0.5) * 0.2, 0),
        active: false,
      });
    }
    return data;
  }, []);

  const panicLevel = useOmniStore((state) => state.panicLevel);
  const prevPanic = useRef(0);

  useFrame((state, delta) => {
    // 1. Order Book rendering
    if (meshRef.current) {
      const count = orderBook.bids.length + orderBook.asks.length;
      meshRef.current.count = count;
      
      let i = 0;
      orderBook.bids.forEach((bid, index) => {
        const x = - (20 - index) * 0.5 - 1; 
        const height = bid.size * 0.05;
        const y = height / 2;
        
        // Shake logic if panic is high
        const shakeX = x + (Math.random() - 0.5) * panicLevel * 0.5;
        const shakeY = y + (Math.random() - 0.5) * panicLevel * 0.5;
        
        dummy.position.set(shakeX, shakeY, 0);
        dummy.scale.set(0.4, height, 0.4);
        dummy.updateMatrix();
        
        meshRef.current!.setMatrixAt(i, dummy.matrix);
        meshRef.current!.setColorAt(i, new THREE.Color(0x00F0FF));
        i++;
      });

      orderBook.asks.forEach((ask, index) => {
        const x = index * 0.5 + 1; 
        const height = ask.size * 0.05;
        const y = height / 2;
        
        const shakeX = x + (Math.random() - 0.5) * panicLevel * 0.5;
        const shakeY = y + (Math.random() - 0.5) * panicLevel * 0.5;
        
        dummy.position.set(shakeX, shakeY, 0);
        dummy.scale.set(0.4, height, 0.4);
        dummy.updateMatrix();
        
        meshRef.current!.setMatrixAt(i, dummy.matrix);
        meshRef.current!.setColorAt(i, new THREE.Color(0xFF0055)); // Blood Red for Asks/Rekt
        i++;
      });

      meshRef.current.instanceMatrix.needsUpdate = true;
      if (meshRef.current.instanceColor) {
        meshRef.current.instanceColor.needsUpdate = true;
      }
    }

    // 2. Particle Physics Trigger
    if (panicLevel > 0.8 && prevPanic.current <= 0.8) {
      // Explode!
      particlesData.forEach((p) => {
        p.active = true;
        p.position.set((Math.random() - 0.5) * 4, Math.random() * 2, (Math.random() - 0.5) * 2);
        p.velocity.set(
          (Math.random() - 0.5) * 15, // vx
          Math.random() * 15 + 5,      // vy
          (Math.random() - 0.5) * 15  // vz
        );
      });
    }
    prevPanic.current = panicLevel;

    // 3. Particle Physics Update
    if (particlesRef.current) {
      particlesData.forEach((p, i) => {
        if (p.active) {
          // Gravity
          p.velocity.y -= 30 * delta; 
          
          p.position.addScaledVector(p.velocity, delta);
          p.rotation.add(p.rotationSpeed);
          
          // Floor collision bounce
          if (p.position.y < 0) {
            p.position.y = 0;
            p.velocity.y *= -0.5; // dampening
            p.velocity.x *= 0.8;
            p.velocity.z *= 0.8;
          }

          // Deactivate if almost stopped
          if (p.position.y === 0 && Math.abs(p.velocity.y) < 1 && Math.abs(p.velocity.x) < 1) {
            p.active = false;
            p.position.y = -10; // hide
          }
        }
        
        particleDummy.position.copy(p.position);
        particleDummy.rotation.set(p.rotation.x, p.rotation.y, p.rotation.z);
        particleDummy.scale.setScalar(Math.random() * 0.3 + 0.1);
        particleDummy.updateMatrix();
        
        particlesRef.current!.setMatrixAt(i, particleDummy.matrix);
        particlesRef.current!.setColorAt(i, new THREE.Color(Math.random() > 0.5 ? 0xFF0055 : 0x00F0FF));
      });
      
      particlesRef.current.instanceMatrix.needsUpdate = true;
      if (particlesRef.current.instanceColor) particlesRef.current.instanceColor.needsUpdate = true;
    }
  });

  return (
    <group position={[0, -2, 0]}>
      <ambientLight intensity={0.5} />
      <directionalLight position={[0, 10, 5]} intensity={1} />
      
      <instancedMesh ref={meshRef} args={[undefined, undefined, totalCount]}>
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial 
          roughness={0.2}
          metalness={0.8}
          transparent={true}
          opacity={0.8}
        />
      </instancedMesh>

      {/* Explosion Particles */}
      <instancedMesh ref={particlesRef} args={[undefined, undefined, particleCount]}>
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial 
          roughness={0.1}
          metalness={1.0}
          emissive={new THREE.Color(0xFF0055)}
          emissiveIntensity={2.0}
        />
      </instancedMesh>
      
      {/* Floor Grid */}
      <gridHelper args={[40, 40, 0x00F0FF, 0x111111]} position={[0, 0, 0]} />
    </group>
  );
};

export default OrderBookTerrain;
