type Numeric = number | null | undefined;

function isMissing(value: Numeric): boolean {
  return value === null || value === undefined || Number.isNaN(value);
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "—";
  }
  return new Date(value).toLocaleString("en-US", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
  });
}

export function formatDuration(seconds: Numeric): string {
  if (isMissing(seconds) || (seconds as number) < 0) {
    return "—";
  }
  const value = seconds as number;
  if (value < 60) {
    return `${value.toFixed(1)}s`;
  }
  const minutes = Math.floor(value / 60);
  const rest = Math.round(value % 60);
  return `${minutes}m ${rest}s`;
}

export function formatMs(value: Numeric): string {
  if (isMissing(value)) {
    return "—";
  }
  return `${Math.round(value as number).toLocaleString("en-US")} ms`;
}

export function formatPercent(value: Numeric, digits = 1): string {
  if (isMissing(value)) {
    return "—";
  }
  return `${(value as number).toFixed(digits)}%`;
}

export function formatConfidence(value: Numeric): string {
  if (isMissing(value)) {
    return "—";
  }
  return `${Math.round((value as number) * 100)}%`;
}

export function categoryLabel(category: string): string {
  return category
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
