import { ESPECIFICACAO_PROCEDENCIA, type OrigemOuVazio } from "../lib/procedencia";

export function ProcedenciaSquare({ origem, titulo }: { origem: OrigemOuVazio; titulo?: string }) {
  const spec = ESPECIFICACAO_PROCEDENCIA[origem];
  return (
    <span
      title={titulo ?? spec.rotulo}
      className="inline-block h-[11px] w-[11px] rounded-[2px]"
      style={{
        backgroundColor: spec.quadradoBg,
        border: `1px ${spec.quadradoTracejado ? "dashed" : "solid"} ${spec.quadradoBorda}`,
      }}
    />
  );
}
