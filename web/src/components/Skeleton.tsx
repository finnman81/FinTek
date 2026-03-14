export function Skeleton({ className = '' }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded-md bg-gray-200 ${className}`}
      aria-hidden="true"
    />
  );
}

export function StatCardSkeleton() {
  return (
    <div className="rounded-lg border border-gray-100 bg-anchor-light/50 p-3">
      <Skeleton className="h-3 w-20 mb-2" />
      <Skeleton className="h-6 w-12" />
    </div>
  );
}

export function DocumentRowSkeleton() {
  return (
    <div className="flex items-center justify-between px-5 py-3">
      <div className="flex items-center gap-2.5">
        <Skeleton className="h-6 w-6 rounded" />
        <Skeleton className="h-4 w-32" />
      </div>
      <Skeleton className="h-5 w-20 rounded-full" />
    </div>
  );
}
