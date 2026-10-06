import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#05050A] flex items-center justify-center p-4">
      {/* Grid background */}
      <div
        className="fixed inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,0,85,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(255,0,85,0.3) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      <div className="text-center space-y-6 relative">
        <h1
          className="font-orbitron text-8xl font-bold text-[#FF0055]"
          style={{ textShadow: "0 0 40px rgba(255,0,85,0.4)" }}
        >
          404
        </h1>
        <p
          className="font-orbitron text-lg tracking-[0.3em] text-[#00F0FF]"
          style={{ textShadow: "0 0 10px rgba(0,240,255,0.5)" }}
        >
          SEÑAL PERDIDA
        </p>
        <p className="font-mono text-xs text-[rgba(255,255,255,0.4)]">
          La ruta solicitada no existe en este nodo de la red cuántica.
        </p>
        <Link
          href="/"
          className="inline-block mt-4 px-6 py-3 border border-[#00F0FF] text-[#00F0FF] font-orbitron text-xs font-bold rounded-lg hover:bg-[rgba(0,240,255,0.1)] hover:shadow-[0_0_20px_rgba(0,240,255,0.3)] transition-all duration-300"
        >
          VOLVER AL COMMAND CENTER
        </Link>
      </div>
    </div>
  );
}
