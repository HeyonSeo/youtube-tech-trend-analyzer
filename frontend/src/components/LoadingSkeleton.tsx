export function CardSkeleton() {
  return (
    <div className="bg-white dark:bg-[#1e293b] rounded-xl p-5 border border-gray-200 dark:border-[#334155] animate-pulse">
      <div className="flex items-center justify-between mb-3">
        <div className="h-4 w-16 bg-gray-200 dark:bg-[#334155] rounded" />
        <div className="w-8 h-8 bg-gray-200 dark:bg-[#334155] rounded-lg" />
      </div>
      <div className="h-8 w-24 bg-gray-200 dark:bg-[#334155] rounded mb-2" />
      <div className="h-3 w-20 bg-gray-200 dark:bg-[#334155] rounded" />
    </div>
  );
}

export function ChartSkeleton() {
  return (
    <div className="bg-white dark:bg-[#1e293b] rounded-xl p-6 border border-gray-200 dark:border-[#334155] animate-pulse">
      <div className="h-5 w-32 bg-gray-200 dark:bg-[#334155] rounded mb-4" />
      <div className="h-[280px] bg-gray-200 dark:bg-[#334155]/50 rounded-lg" />
    </div>
  );
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="bg-white dark:bg-[#1e293b] rounded-xl border border-gray-200 dark:border-[#334155] overflow-hidden animate-pulse">
      <div className="px-6 py-4 border-b border-gray-200 dark:border-[#334155]">
        <div className="h-5 w-40 bg-gray-200 dark:bg-[#334155] rounded" />
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="px-6 py-4 border-b border-gray-200 dark:border-[#334155] flex gap-4">
          <div className="h-4 w-8 bg-gray-200 dark:bg-[#334155] rounded" />
          <div className="h-4 w-24 bg-gray-200 dark:bg-[#334155] rounded" />
          <div className="h-4 flex-1 bg-gray-200 dark:bg-[#334155] rounded" />
          <div className="h-4 w-20 bg-gray-200 dark:bg-[#334155] rounded" />
        </div>
      ))}
    </div>
  );
}
