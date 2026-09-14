"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export function AutoRefresh({
  active,
  intervalMs = 10000,
}: {
  active: boolean;
  intervalMs?: number;
}) {
  const router = useRouter();

  useEffect(() => {
    if (!active) {
      return;
    }
    const timer = setInterval(() => router.refresh(), intervalMs);
    return () => clearInterval(timer);
  }, [active, intervalMs, router]);

  if (!active) {
    return null;
  }

  return (
    <span className="inline-flex items-center gap-2 text-xs text-zinc-400">
      <span className="relative flex h-2 w-2">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-70" />
        <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
      </span>
      Live update
    </span>
  );
}
