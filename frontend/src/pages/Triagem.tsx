import { useNavigate, useSearchParams } from "react-router-dom";

import { useFacetas } from "../api/hooks/useFacetas";
import type { ImoveisFiltros } from "../api/hooks/useImoveis";
import { useImoveis } from "../api/hooks/useImoveis";
import { useTriagemKpis } from "../api/hooks/useTriagemKpis";
import { apiPost } from "../api/client";
import type { ImovelListItem } from "../api/types";
import { FiltroPainel } from "../components/FiltroPainel";
import { MoneyValue } from "../components/MoneyValue";
import { ProcedenciaSquare } from "../components/ProcedenciaSquare";
import { formatArea, formatPercent } from "../lib/format";
import { useQueryClient } from "@tanstack/react-query";

const CHAVES_RESUMO = ["valor_mercado", "iptu_atraso", "condominio_atraso", "ocupacao", "reforma"] as const;
const ROTULO_CHAVE: Record<(typeof CHAVES_RESUMO)[number], string> = {
  valor_mercado: "mercado",
  iptu_atraso: "IPTU",
  condominio_atraso: "condomínio",
  ocupacao: "ocupação",
  reforma: "reforma",
};

function filtrosDeParams(params: URLSearchParams): ImoveisFiltros {
  return {
    uf: params.get("uf") ?? undefined,
    cidade: params.get("cidade") ?? undefined,
    bairro: params.get("bairro") ?? undefined,
    preco_min: params.get("preco_min") ? Number(params.get("preco_min")) : undefined,
    preco_max: params.get("preco_max") ? Number(params.get("preco_max")) : undefined,
    tipo: params.getAll("tipo").length ? params.getAll("tipo") : undefined,
    financiamento: (params.get("financiamento") as ImoveisFiltros["financiamento"]) ?? undefined,
    fgts: (params.get("fgts") as ImoveisFiltros["fgts"]) ?? undefined,
    desconto_min: params.get("desconto_min") ? Number(params.get("desconto_min")) : undefined,
    sem_dados_campo: params.get("sem_dados_campo") === "true" ? true : undefined,
  };
}

function paramsDeFiltros(filtros: ImoveisFiltros): URLSearchParams {
  const params = new URLSearchParams();
  if (filtros.uf) params.set("uf", filtros.uf);
  if (filtros.cidade) params.set("cidade", filtros.cidade);
  if (filtros.bairro) params.set("bairro", filtros.bairro);
  if (filtros.preco_min) params.set("preco_min", String(filtros.preco_min));
  if (filtros.preco_max) params.set("preco_max", String(filtros.preco_max));
  for (const tipo of filtros.tipo ?? []) params.append("tipo", tipo);
  if (filtros.financiamento && filtros.financiamento !== "indiferente") params.set("financiamento", filtros.financiamento);
  if (filtros.fgts && filtros.fgts !== "indiferente") params.set("fgts", filtros.fgts);
  if (filtros.desconto_min) params.set("desconto_min", String(filtros.desconto_min));
  if (filtros.sem_dados_campo) params.set("sem_dados_campo", "true");
  return params;
}

function descricaoFiltros(filtros: ImoveisFiltros): string {
  const partes: string[] = [];
  if (filtros.cidade) partes.push(filtros.cidade);
  if (filtros.bairro) partes.push(`bairro "${filtros.bairro}"`);
  if (filtros.desconto_min) partes.push(`desconto ≥ ${filtros.desconto_min}%`);
  if (filtros.preco_min || filtros.preco_max) partes.push("faixa de preço ajustada");
  if (filtros.tipo?.length) partes.push(filtros.tipo.join(", "));
  if (filtros.financiamento && filtros.financiamento !== "indiferente")
    partes.push(filtros.financiamento === "aceita" ? "aceita financiamento" : "não aceita financiamento");
  if (filtros.fgts && filtros.fgts !== "indiferente")
    partes.push(filtros.fgts === "aceita" ? "aceita FGTS" : "não aceita FGTS");
  if (filtros.sem_dados_campo) partes.push("sem dados de campo");
  return partes.length ? `Filtrando por ${partes.join(" · ")}` : "Sem filtros: mostrando toda a base";
}

function notaDadosDeCampo(item: ImovelListItem): string {
  const { preenchidos, total, faltando } = item.resumo_campos;
  if (preenchidos === total) return "completo";
  if (preenchidos === 0) return "avaliação não iniciada";
  return `falta ${faltando.map((c) => ROTULO_CHAVE[c as (typeof CHAVES_RESUMO)[number]] ?? c).join(" e ")}`;
}

function corContador(preenchidos: number, total: number): string {
  if (preenchidos === total) return "text-green";
  if (preenchidos === 0) return "text-labelSoft";
  return "text-amber";
}

function corDesconto(desconto: string | null): string {
  const valor = desconto ? Number(desconto) : null;
  if (valor === null) return "text-label";
  if (valor >= 45) return "text-green";
  if (valor >= 35) return "text-ink";
  return "text-label";
}

export function Triagem() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const filtros = filtrosDeParams(searchParams);
  const kpis = useTriagemKpis();
  const { data: facetas } = useFacetas();
  const { data, isLoading } = useImoveis(filtros);

  function atualizarFiltros(patch: Partial<ImoveisFiltros>) {
    setSearchParams(paramsDeFiltros({ ...filtros, ...patch }));
  }

  async function cortar(item: ImovelListItem, e: React.MouseEvent) {
    e.stopPropagation();
    const motivo = window.prompt(`Motivo do descarte de "${item.endereco}":`);
    if (!motivo) return;
    await apiPost(`/avaliacoes/${item.avaliacao_id}/descartar`, { motivo });
    queryClient.invalidateQueries({ queryKey: ["imoveis"] });
  }

  const kpiItens = [
    { label: "Não avaliados", valor: kpis.naoAvaliados, cor: "" },
    { label: "Com dados de campo", valor: kpis.comDadosDeCampo, cor: "" },
    { label: "Prontos p/ decisão", valor: kpis.prontosParaDecisao, cor: "text-green" },
    { label: "Desconto ≥ 40%", valor: kpis.descontoMaiorIgual40, cor: "" },
  ];

  return (
    <div className="p-[24px_28px_60px]">
      <div className="mb-[18px] flex flex-wrap items-end justify-between gap-6">
        <div>
          <div className="mb-[6px] font-mono text-[10.5px] uppercase tracking-[0.18em] text-label">
            Fila de triagem
          </div>
          <h1 className="m-0 font-serif text-[30px] font-semibold tracking-[-0.015em]">
            O que vale a pena visitar e pesquisar
          </h1>
        </div>
        <div className="grid grid-cols-4 gap-[26px]">
          {kpiItens.map((k) => (
            <div key={k.label} className="text-right">
              <div className="font-mono text-[9.5px] uppercase tracking-[0.13em] text-label">{k.label}</div>
              <div className={`mt-[3px] font-serif text-[23px] font-semibold tracking-[-0.01em] ${k.cor}`}>
                {k.valor ?? "…"}
              </div>
            </div>
          ))}
        </div>
      </div>

      <FiltroPainel
        filtros={filtros}
        onChange={atualizarFiltros}
        onLimpar={() => setSearchParams(new URLSearchParams())}
        cidades={facetas?.cidades ?? []}
      />

      <div className="mb-3 flex items-center justify-between gap-4">
        <span className="text-[13px] text-textMuted">{descricaoFiltros(filtros)}</span>
        <span className="font-mono text-[11px] text-label">
          {data ? `${data.total} de ${kpis.totalGeral ?? data.total} imóveis` : ""}
        </span>
      </div>

      <div className="overflow-hidden rounded-md border border-border bg-surface">
        <div className="grid grid-cols-[2.4fr_0.75fr_1fr_1fr_0.7fr_1.15fr_1.35fr_0.95fr] gap-[14px] bg-surface2 px-[18px] py-2 font-mono text-[9.5px] uppercase tracking-[0.13em] text-label">
          <div>Imóvel</div>
          <div>Tipo</div>
          <div className="text-right">Preço</div>
          <div className="text-right">Avaliação</div>
          <div className="text-right">Desc.</div>
          <div>Modalidade</div>
          <div>Dados de campo</div>
          <div className="text-right">Triagem</div>
        </div>

        {isLoading && <div className="p-[38px] text-center text-[13px] text-textSoft">Carregando…</div>}

        {!isLoading && data?.items.length === 0 && (
          <div className="p-[38px] text-center">
            <div className="text-[13px] text-textSoft">Nenhum imóvel atende a esses filtros.</div>
            <div className="mt-1 text-[11.5px] text-labelSoft">
              Tente ampliar a faixa de preço ou reduzir o desconto mínimo.
            </div>
            <button
              type="button"
              onClick={() => setSearchParams(new URLSearchParams())}
              className="mt-3 rounded-pill border border-border2 px-3 py-[6px] font-serif text-[12.5px] text-ink3"
            >
              Limpar filtros
            </button>
          </div>
        )}

        {data?.items.map((item) => (
          <div
            key={item.lote_id}
            onClick={() => navigate(`/imoveis/${item.lote_id}`)}
            className="grid cursor-pointer grid-cols-[2.4fr_0.75fr_1fr_1fr_0.7fr_1.15fr_1.35fr_0.95fr] items-center gap-[14px] border-t border-divider px-[18px] py-[13px] hover:bg-surface3"
          >
            <div className="min-w-0">
              <div className="truncate text-[14px]">{item.endereco}</div>
              <div className="truncate font-mono text-[10.5px] text-label">
                {item.codigo_externo} · {item.cidade.toUpperCase()} · {(item.bairro ?? "").toUpperCase()} ·{" "}
                {formatArea(item.area_privativa_m2)}
                {item.quartos ? ` · ${item.quartos}q` : ""}
              </div>
            </div>
            <div className="text-[13px] capitalize">{item.tipo}</div>
            <MoneyValue value={item.preco_venda} className="text-right text-[12.5px]" />
            <MoneyValue value={item.valor_avaliacao} className="text-right text-[12.5px] text-textMuted" />
            <div className={`text-right font-mono text-[12.5px] font-semibold ${corDesconto(item.desconto_pct)}`}>
              {item.desconto_pct ? formatPercent(item.desconto_pct) : "—"}
            </div>
            <div className="min-w-0">
              <div className="truncate text-[12px]">{item.modalidade ?? "—"}</div>
              <div className="truncate font-mono text-[10px] text-labelSoft">
                {[item.aceita_financiamento ? "aceita financiamento" : null, item.aceita_fgts === "aceita" ? "aceita fgts" : null]
                  .filter(Boolean)
                  .join(" · ")}
              </div>
            </div>
            <div>
              <div className="mb-1 flex items-center gap-1">
                {CHAVES_RESUMO.map((chave) => (
                  <ProcedenciaSquare
                    key={chave}
                    origem={item.resumo_campos.faltando.includes(chave) ? "vazio" : "manual"}
                    titulo={ROTULO_CHAVE[chave]}
                  />
                ))}
                <span
                  className={`ml-1 font-mono text-[10.5px] ${corContador(item.resumo_campos.preenchidos, item.resumo_campos.total)}`}
                >
                  {item.resumo_campos.preenchidos}/{item.resumo_campos.total}
                </span>
              </div>
              <div className="truncate text-[11px] text-label">{notaDadosDeCampo(item)}</div>
            </div>
            <div className="flex justify-end gap-[6px]">
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/imoveis/${item.lote_id}`);
                }}
                className="rounded-sm border border-greenBorder bg-greenBg px-2 py-1 text-[11.5px] text-green"
              >
                Preencher
              </button>
              <button
                type="button"
                onClick={(e) => cortar(item, e)}
                className="rounded-sm border border-border bg-redBg px-2 py-1 text-[11.5px] text-red"
              >
                Corta
              </button>
            </div>
          </div>
        ))}

        <div className="flex items-center justify-between border-t border-divider px-[18px] py-2 font-mono text-[11px] text-label">
          <span>Ordenado por desconto</span>
          <span>Nenhuma automação ativa · todos os dados de campo são manuais</span>
        </div>
      </div>
    </div>
  );
}
