"use client";

import React, { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";

function LoginForm() {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
  const from = searchParams.get("from") || "/";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });

      if (res.ok) {
        router.push(from);
        router.refresh();
      } else {
        const data = await res.json();
        setError(data.error || "Authentication failed");
      }
    } catch {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#05050A] flex items-center justify-center p-4">
      {/* Background grid effect */}
      <div
        className="fixed inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(rgba(0,240,255,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(0,240,255,0.3) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      <div className="w-full max-w-md relative">
        {/* Glow effect behind card */}
        <div className="absolute -inset-1 bg-gradient-to-r from-[#00F0FF20] via-[#8B00FF20] to-[#00F0FF20] rounded-2xl blur-xl" />

        <div className="relative border border-[rgba(0,240,255,0.3)] bg-[rgba(5,15,25,0.8)] backdrop-blur-xl rounded-2xl p-8 space-y-8">
          {/* Logo */}
          <div className="text-center space-y-2">
            <h1
              className="font-orbitron text-3xl font-bold tracking-tight text-white"
              style={{ textShadow: "0 0 20px rgba(0,240,255,0.5)" }}
            >
              CHRONOS
            </h1>
            <p className="font-orbitron text-[10px] tracking-[0.3em] text-[#8B00FF]">
              QUANTUM TERMINAL
            </p>
            <div className="w-16 h-[1px] bg-gradient-to-r from-transparent via-[#00F0FF] to-transparent mx-auto mt-4" />
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <label className="block font-mono text-[9px] text-[rgba(255,255,255,0.5)] tracking-widest uppercase">
                Terminal Access Code
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter admin password..."
                autoFocus
                className="w-full bg-[rgba(0,0,0,0.4)] border border-[rgba(0,240,255,0.2)] rounded-lg px-4 py-3 font-mono text-sm text-white placeholder-[rgba(255,255,255,0.2)] outline-none focus:border-[#00F0FF] focus:shadow-[0_0_15px_rgba(0,240,255,0.2)] transition-all"
              />
            </div>

            {error && (
              <div className="p-3 border border-[#FF0055] bg-[rgba(255,0,85,0.1)] rounded-lg">
                <p className="font-mono text-xs text-[#FF0055]">
                  ⚠ {error}
                </p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !password}
              className="w-full py-3 rounded-lg font-orbitron text-sm font-bold tracking-wider border border-[#00F0FF] text-[#00F0FF] bg-[rgba(0,240,255,0.05)] hover:bg-[rgba(0,240,255,0.15)] hover:shadow-[0_0_20px_rgba(0,240,255,0.3)] disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-300"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-[#00F0FF] border-t-transparent rounded-full animate-spin" />
                  AUTHENTICATING...
                </span>
              ) : (
                "AUTHORIZE ACCESS"
              )}
            </button>
          </form>

          {/* Footer */}
          <p className="text-center font-mono text-[8px] text-[rgba(255,255,255,0.2)]">
            ENCRYPTED CHANNEL • AES-256 • SECURE SESSION
          </p>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#05050A] flex items-center justify-center">
          <span className="font-mono text-[#00F0FF] animate-pulse">
            Loading...
          </span>
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
