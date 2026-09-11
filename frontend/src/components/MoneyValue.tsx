import { formatMoney } from "../lib/format";

export function MoneyValue({
  value,
  className = "",
}: {
  value: string | number | null | undefined;
  className?: string;
}) {
  return <span className={`font-mono ${className}`}>{formatMoney(value)}</span>;
}
