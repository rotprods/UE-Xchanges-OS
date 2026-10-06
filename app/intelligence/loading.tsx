export default function IntelligenceLoading() {
  return (
    <div className="p-6 space-y-6 animate-pulse">
      <div className="h-10 w-64 bg-[rgba(0,240,255,0.05)] rounded-lg" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div
            key={i}
            className="h-48 bg-[rgba(0,240,255,0.03)] border border-[rgba(0,240,255,0.1)] rounded-xl"
          />
        ))}
      </div>
    </div>
  );
}
