import type { ImoveisFiltros } from "../api/hooks/useImoveis";

const TIPOS = [
  { valor: "casa", rotulo: "Casa" },
  { valor: "apartamento", rotulo: "Apartamento" },
  { valor: "terreno", rotulo: "Terreno" },
  { valor: "loja", rotulo: "Loja" },
];

const SEGMENTOS = [
  { valor: "indiferente", rotulo: "Indiferente" },
  { valor: "aceita", rotulo: "Aceita" },
  { valor: "nao_aceita", rotulo: "Não aceita" },
] as const;

const PRECO_MAX_FAIXA = 1_600_000;

function rotuloDesconto(valor: number | undefined): string {
  return valor && valor > 0 ? `≥ ${valor}%` : "qualquer";
}

function rotuloPreco(valor: number): string {
  return valor >= PRECO_MAX_FAIXA ? "R$ 1.600.000+" : `R$ ${valor.toLocaleString("pt-BR")}`;
}

const rotuloCampo = "font-mono text-[9.5px] uppercase tracking-[0.13em] text-label";
const inputBase =
  "w-full min-w-0 rounded-sm border border-border2 bg-white px-[9px] py-[7px] text-[13px] text-ink";
const pill = "rounded-pill border px-3 py-[6px] font-serif text-[12.5px] cursor-pointer transition-colors";

interface Props {
  filtros: ImoveisFiltros;
  onChange: (patch: Partial<ImoveisFiltros>) => void;
  onLimpar: () => void;
  cidades: string[];
}

export function FiltroPainel({ filtros, onChange, onLimpar, cidades }: Props) {
  const tipos = filtros.tipo ?? [];
  const precoMin = filtros.preco_min ?? 0;
  const precoMax = filtros.preco_max ?? PRECO_MAX_FAIXA;
  const bandaLeft = `${(precoMin / PRECO_MAX_FAIXA) * 100}%`;
  const bandaRight = `${100 - (precoMax / PRECO_MAX_FAIXA) * 100}%`;

  return (
    <div className="mb-[14px] rounded-md border border-border bg-surface p-[16px_18px]">
      <div className="mb-[15px] flex flex-wrap items-center justify-between gap-4">
        <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-label">Buscar imóveis</span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onChange({ sem_dados_campo: !filtros.sem_dados_campo })}
            className={`${pill} ${
              filtros.sem_dados_campo ? "border-ink bg-ink text-onDark" : "border-border2 bg-transparent text-ink3"
            }`}
          >
            Só sem dados de campo
          </button>
          <button
            type="button"
            onClick={() => onChange({ ocultar_descartados: !filtros.ocultar_descartados })}
            className={`${pill} ${
              filtros.ocultar_descartados ? "border-ink bg-ink text-onDark" : "border-border2 bg-transparent text-ink3"
            }`}
          >
            Ocultar descartados
          </button>
          <button
            type="button"
            onClick={onLimpar}
            className={`${pill} border-border2 bg-transparent text-ink3 hover:bg-[#E6E3DA]`}
          >
            Limpar filtros
          </button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-x-[18px] gap-y-4">
        <div>
          <div className={`mb-[6px] ${rotuloCampo}`}>
            Estado <span className="normal-case tracking-normal text-labelSoft">· só MG na base</span>
          </div>
          <select
            className={inputBase}
            value={filtros.uf ?? ""}
            onChange={(e) => onChange({ uf: e.target.value || undefined })}
          >
            <option value="">Todos os estados</option>
            <option value="MG">MG</option>
          </select>
        </div>

        <div>
          <div className={`mb-[6px] ${rotuloCampo}`}>Cidade</div>
          <select
            className={inputBase}
            value={filtros.cidade ?? ""}
            onChange={(e) => onChange({ cidade: e.target.value || undefined })}
          >
            <option value="">Todas as cidades</option>
            {cidades.map((cidade) => (
              <option key={cidade} value={cidade}>
                {cidade}
              </option>
            ))}
          </select>
        </div>

        <div>
          <div className={`mb-[6px] ${rotuloCampo}`}>Bairro</div>
          <input
            className={inputBase}
            placeholder="parte do nome"
            value={filtros.bairro ?? ""}
            onChange={(e) => onChange({ bairro: e.target.value || undefined })}
          />
        </div>

        <div>
          <div className={`mb-[6px] ${rotuloCampo}`}>
            Desconto mínimo <span className="normal-case tracking-normal text-labelSoft">· valor da planilha</span>
          </div>
          <div className="flex items-center gap-[10px]">
            <input
              type="range"
              min={0}
              max={75}
              step={5}
              className="min-w-0 flex-1 accent-green"
              value={filtros.desconto_min ?? 0}
              onChange={(e) => onChange({ desconto_min: Number(e.target.value) || undefined })}
            />
            <span className="whitespace-nowrap font-mono text-[12.5px] font-semibold text-green">
              {rotuloDesconto(filtros.desconto_min)}
            </span>
          </div>
        </div>

        <div className="col-span-2">
          <div className="mb-[6px] flex items-baseline justify-between gap-3">
            <span className={rotuloCampo}>Faixa de preço</span>
            <span className="font-mono text-[12px]">
              {rotuloPreco(precoMin)} <span className="text-labelSoft">até</span> {rotuloPreco(precoMax)}
            </span>
          </div>
          <div className="relative my-[9px] h-1 rounded-[2px] bg-dividerDash">
            <div className="absolute top-0 bottom-0 rounded-[2px] bg-green" style={{ left: bandaLeft, right: bandaRight }} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <input
              type="range"
              min={0}
              max={PRECO_MAX_FAIXA}
              step={10_000}
              className="w-full min-w-0 accent-green"
              value={precoMin}
              onChange={(e) => onChange({ preco_min: Number(e.target.value) || undefined })}
            />
            <input
              type="range"
              min={0}
              max={PRECO_MAX_FAIXA}
              step={10_000}
              className="w-full min-w-0 accent-green"
              value={precoMax}
              onChange={(e) => onChange({ preco_max: Number(e.target.value) || undefined })}
            />
          </div>
        </div>

        <div className="col-span-2">
          <div className={`mb-[6px] ${rotuloCampo}`}>Tipo de imóvel</div>
          <div className="flex flex-wrap gap-[6px]">
            {TIPOS.map((t) => {
              const ativo = tipos.includes(t.valor);
              return (
                <button
                  key={t.valor}
                  type="button"
                  onClick={() =>
                    onChange({
                      tipo: ativo ? tipos.filter((v) => v !== t.valor) : [...tipos, t.valor],
                    })
                  }
                  className={`${pill} ${ativo ? "border-ink bg-ink text-onDark" : "border-border2 bg-transparent text-ink3"}`}
                >
                  {t.rotulo}
                </button>
              );
            })}
          </div>
        </div>

        <div className="col-span-2">
          <div className={`mb-[6px] ${rotuloCampo}`}>Financiamento</div>
          <div className="grid grid-cols-3 gap-[6px]">
            {SEGMENTOS.map((s) => (
              <button
                key={s.valor}
                type="button"
                onClick={() => onChange({ financiamento: s.valor })}
                className={`rounded-sm border px-2 py-[6px] font-serif text-[12.5px] ${
                  (filtros.financiamento ?? "indiferente") === s.valor
                    ? "border-ink bg-ink text-onDark"
                    : "border-border2 bg-transparent text-ink3"
                }`}
              >
                {s.rotulo}
              </button>
            ))}
          </div>
        </div>

        <div className="col-span-2">
          <div className={`mb-[6px] ${rotuloCampo}`}>
            FGTS <span className="normal-case tracking-normal text-labelSoft">· dado manual, não vem na planilha</span>
          </div>
          <div className="grid grid-cols-3 gap-[6px]">
            {SEGMENTOS.map((s) => (
              <button
                key={s.valor}
                type="button"
                onClick={() => onChange({ fgts: s.valor })}
                className={`rounded-sm border px-2 py-[6px] font-serif text-[12.5px] ${
                  (filtros.fgts ?? "indiferente") === s.valor
                    ? "border-ink bg-ink text-onDark"
                    : "border-border2 bg-transparent text-ink3"
                }`}
              >
                {s.rotulo}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
