"use client";

import React, { useEffect, useState, useRef } from "react";
import Peer, { DataConnection } from "peerjs";

interface CursorPos {
  x: number;
  y: number;
}

export default function SwarmManager() {
  const [peerId, setPeerId] = useState<string | null>(null);
  const [targetId, setTargetId] = useState<string>("");
  const [connections, setConnections] = useState<DataConnection[]>([]);
  const [remoteCursors, setRemoteCursors] = useState<Record<string, CursorPos>>({});
  const peerRef = useRef<Peer | null>(null);
  // Use ref so mousemove handler always has fresh connections without re-running effect
  const connectionsRef = useRef<DataConnection[]>([]);

  // Keep ref in sync with state
  useEffect(() => {
    connectionsRef.current = connections;
  }, [connections]);

  useEffect(() => {
    // Initialize Peer
    const peer = new Peer();
    peerRef.current = peer;

    peer.on("open", (id) => {
      setPeerId(id);
    });

    peer.on("connection", (conn) => {
      setupConnection(conn);
    });

    const handleMouseMove = (e: MouseEvent) => {
      const pos = { x: e.clientX / window.innerWidth, y: e.clientY / window.innerHeight };
      // Use ref instead of stale state closure
      connectionsRef.current.forEach((conn) => {
        if (conn.open) {
          conn.send({ type: "CURSOR", pos });
        }
      });
    };

    window.addEventListener("mousemove", handleMouseMove);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      peer.destroy();
    };
  }, []); // Empty deps — peer only initializes once

  const setupConnection = (conn: DataConnection) => {
    conn.on("open", () => {
      setConnections((prev) => [...prev, conn]);
    });

    conn.on("data", (data: any) => {
      if (data.type === "CURSOR" && data.pos) {
        setRemoteCursors((prev) => ({
          ...prev,
          [conn.peer]: data.pos,
        }));
      }
    });

    conn.on("close", () => {
      setConnections((prev) => prev.filter((c) => c.peer !== conn.peer));
      setRemoteCursors((prev) => {
        const next = { ...prev };
        delete next[conn.peer];
        return next;
      });
    });
  };

  const connectToPeer = () => {
    if (!peerRef.current || !targetId) return;
    const conn = peerRef.current.connect(targetId);
    setupConnection(conn);
    setTargetId("");
  };

  return (
    <>
      {/* Cursors Render */}
      {Object.entries(remoteCursors).map(([id, pos]) => (
        <div
          key={id}
          className="fixed z-[100] pointer-events-none transition-all duration-75 ease-linear"
          style={{
            left: `${pos.x * 100}vw`,
            top: `${pos.y * 100}vh`,
          }}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M4.5 3L18.5 10L11.5 12.5L9.5 19.5L4.5 3Z" fill="#00F0FF" stroke="#00F0FF" strokeWidth="2" strokeLinejoin="round"/>
          </svg>
          <span className="absolute left-6 top-6 text-[10px] font-mono text-[#00F0FF] bg-[rgba(0,240,255,0.1)] px-1 rounded backdrop-blur">
            {id.substring(0, 4)}
          </span>
        </div>
      ))}

      {/* Swarm UI Panel */}
      <div className="glass-panel border border-[rgba(0,240,255,0.3)] p-4 rounded-xl flex flex-col space-y-3 relative overflow-hidden mt-4">
        <h3 className="font-orbitron font-bold text-[#00F0FF] text-[10px] tracking-widest flex items-center">
          <span className="w-1.5 h-1.5 bg-[#00F0FF] rounded-full mr-2 animate-pulse" />
          SWARM NETWORK {connections.length > 0 && `(${connections.length} PEERS)`}
        </h3>
        
        <div className="flex justify-between items-center bg-[rgba(0,0,0,0.4)] p-2 rounded border border-[rgba(255,255,255,0.05)]">
          <span className="font-mono text-[9px] text-[rgba(255,255,255,0.4)]">NODE ID</span>
          <span className="font-mono text-[10px] text-[#00F0FF] select-all cursor-pointer">
            {peerId || "CONNECTING..."}
          </span>
        </div>

        <div className="flex space-x-2">
          <input
            type="text"
            placeholder="Target Node ID..."
            value={targetId}
            onChange={(e) => setTargetId(e.target.value)}
            className="flex-1 bg-[rgba(0,240,255,0.05)] border border-[rgba(0,240,255,0.3)] text-white font-mono text-[10px] p-2 rounded outline-none focus:border-[#00F0FF]"
          />
          <button
            onClick={connectToPeer}
            className="bg-[rgba(0,240,255,0.1)] border border-[#00F0FF] text-[#00F0FF] text-[10px] px-3 font-orbitron font-bold rounded hover:bg-[rgba(0,240,255,0.2)] transition-colors"
          >
            LINK
          </button>
        </div>
      </div>
    </>
  );
}
