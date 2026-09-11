import { formatPercent } from "../lib/format";

export function PercentValue({
  value,
  withSign = false,
  className = "",
}: {
  value: string | number | null | undefined;
  withSign?: boolean;
  className?: string;
}) {
  return <span className={`font-mono ${className}`}>{formatPercent(value, { withSign })}</span>;
}
