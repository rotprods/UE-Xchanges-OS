export default function TradingLoading() {
  return (
    <div className="p-6 space-y-6 animate-pulse">
      <div className="h-10 w-56 bg-[rgba(0,240,255,0.05)] rounded-lg" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 h-[400px] bg-[rgba(0,240,255,0.03)] border border-[rgba(0,240,255,0.1)] rounded-xl" />
        <div className="h-[400px] bg-[rgba(0,240,255,0.03)] border border-[rgba(0,240,255,0.1)] rounded-xl" />
      </div>
      <div className="h-64 bg-[rgba(0,240,255,0.03)] border border-[rgba(0,240,255,0.1)] rounded-xl" />
    </div>
  );
}
