import { ESPECIFICACAO_PROCEDENCIA, type OrigemOuVazio } from "../lib/procedencia";

export function ProcedenciaChip({ origem }: { origem: OrigemOuVazio }) {
  const spec = ESPECIFICACAO_PROCEDENCIA[origem];
  return (
    <span
      className="inline-block rounded-sm px-2 py-[2px] font-mono text-[9.5px] uppercase tracking-[0.1em]"
      style={{ backgroundColor: spec.chipBg, color: spec.chipTexto }}
    >
      {spec.rotulo}
    </span>
  );
}
