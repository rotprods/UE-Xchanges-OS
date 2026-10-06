export default function ChartsLoading() {
  return (
    <div className="p-6 space-y-4 animate-pulse">
      <div className="h-8 w-48 bg-[rgba(0,240,255,0.05)] rounded-lg" />
      <div className="flex gap-2">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-10 w-20 bg-[rgba(0,240,255,0.05)] rounded-lg" />
        ))}
      </div>
      <div className="h-[500px] bg-[rgba(0,240,255,0.03)] border border-[rgba(0,240,255,0.1)] rounded-xl" />
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-16 bg-[rgba(0,240,255,0.05)] rounded-lg" />
        ))}
      </div>
    </div>
  );
}
