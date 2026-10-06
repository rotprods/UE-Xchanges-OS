export default function Loading() {
  return (
    <div className="min-h-screen bg-[#05050A] flex flex-col items-center justify-center gap-6">
      {/* Pulsing ring */}
      <div className="relative w-20 h-20">
        <div
          className="absolute inset-0 rounded-full border-2 border-[#00F0FF] animate-ping opacity-30"
        />
        <div
          className="absolute inset-2 rounded-full border-2 border-[#8B00FF] animate-spin"
          style={{ borderTopColor: "transparent", animationDuration: "1.5s" }}
        />
        <div className="absolute inset-4 rounded-full bg-[rgba(0,240,255,0.05)] backdrop-blur-sm flex items-center justify-center">
          <span className="text-[#00F0FF] font-orbitron text-xl font-bold">Q</span>
        </div>
      </div>
      <p
        className="font-orbitron text-[10px] tracking-[0.4em] text-[#00F0FF] animate-pulse"
      >
        INITIALIZING QUANTUM NODE...
      </p>
    </div>
  );
}
