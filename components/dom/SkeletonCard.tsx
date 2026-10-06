"use client";

export default function SkeletonCard({
  width = "100%",
  height = "80px",
  className = "",
}: {
  width?: string;
  height?: string;
  className?: string;
}) {
  return (
    <div
      className={`rounded-xl overflow-hidden ${className}`}
      style={{ width, height }}
    >
      <div
        className="w-full h-full animate-pulse"
        style={{
          background:
            "linear-gradient(90deg, rgba(10,10,20,0.8) 25%, rgba(0,240,255,0.06) 50%, rgba(10,10,20,0.8) 75%)",
          backgroundSize: "200% 100%",
          animation: "shimmer 1.5s infinite",
        }}
      />
      <style jsx>{`
        @keyframes shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>
    </div>
  );
}
