/** Formatação pt-BR conforme docs/README.md "Formatação de número". */

type Num = string | number | null | undefined;

function toNumber(value: Num): number | null {
  if (value === null || value === undefined || value === "") return null;
  const num = typeof value === "string" ? Number(value) : value;
  return Number.isNaN(num) ? null : num;
}

/** "R$ 49.647" — sem centavos; negativo vira "– R$ 11.400" (travessão, não sinal colado). */
export function formatMoney(value: Num): string {
  const num = toNumber(value);
  if (num === null) return "—";
  const abs = Math.round(Math.abs(num));
  const formatado = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 }).format(abs);
  return `${num < 0 ? "– " : ""}R$ ${formatado}`;
}

/** "71,8%" — uma casa decimal, vírgula. `withSign` prefixa "+" quando positivo (ex. "+64,8%"). */
export function formatPercent(value: Num, opts: { withSign?: boolean } = {}): string {
  const num = toNumber(value);
  if (num === null) return "—";
  const sinal = opts.withSign && num > 0 ? "+" : "";
  return `${sinal}${num.toFixed(1).replace(".", ",")}%`;
}

/** "63,96 m²" */
export function formatArea(value: Num): string {
  const num = toNumber(value);
  if (num === null) return "—";
  return `${num.toFixed(2).replace(".", ",")} m²`;
}

/** Inverso de `formatMoney`/`formatPercent`: o usuário digita `3.400` (milhar por ponto) ou
 * `2,5` (decimal por vírgula) — igual ao `parse_decimal_br` do backend (services/numeros.py)
 * — e isso vira o formato canônico (ponto decimal) que os campos `Decimal` da API aceitam. */
export function parseDecimalBr(texto: string): string {
  let t = texto.trim();
  if (t.includes(",")) {
    t = t.replaceAll(".", "").replace(",", ".");
  } else {
    const partes = t.split(".");
    if (partes.length > 1 && partes[partes.length - 1].length === 3 && partes.every((p) => /^\d+$/.test(p))) {
      t = t.replaceAll(".", "");
    }
  }
  return t;
}

export function formatDateTime(value: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatDate(value: string | null): string {
  if (!value) return "—";
  // datas "YYYY-MM-DD" (sem hora) não têm timezone — `new Date(string)` as interpreta como
  // UTC e pode voltar um dia em fusos negativos (ex. Brasil); monta a data em horário local.
  const [ano, mes, dia] = value.split("-").map(Number);
  return new Date(ano, mes - 1, dia).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}
