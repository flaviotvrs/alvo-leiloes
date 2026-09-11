import { useNavigate } from "react-router-dom";

import { useFunil } from "../api/hooks/useFunil";
import type { Etapa, FunilCard as FunilCardType } from "../api/types";
import { ProcedenciaSquare } from "../components/ProcedenciaSquare";
import { formatPercent } from "../lib/format";

const CHAVES_RESUMO = ["valor_mercado", "iptu_atraso", "condominio_atraso", "ocupacao", "reforma"] as const;

const ETAPA_COR: Record<Etapa, string> = {
  nao_avaliado: "#9C978A",
  pesquisa_campo: "#7C7768",
  analise_financeira: "#8A6B14",
  decisao: "#8C2F2F",
  aprovado_lance: "#1F6F4A",
  descartado: "#8C2F2F",
};

const ETAPA_TITULO: Record<Etapa, string> = {
  nao_avaliado: "Não avaliados",
  pesquisa_campo: "Pesquisa de campo",
  analise_financeira: "Análise financeira",
  decisao: "Decisão",
  aprovado_lance: "Aprovado p/ lance",
  descartado: "Descartados",
};

const CARTOES_EDITORIAIS = [
  {
    tag: "Trabalho manual",
    cor: "text-amber",
    titulo: "IPTU e condomínio ainda exigem consulta manual",
    nota: "Toda dívida em atraso depende de visita ao site da prefeitura ou contato com a administradora — nenhuma automação cobre isso hoje.",
  },
  {
    tag: "Ponto cego",
    cor: "text-red",
    titulo: "Ocupação de longa data",
    nota: "Usucapião é o maior risco não coberto pelo score financeiro — depende de verificação em campo, não da planilha.",
  },
  {
    tag: "Próxima automação",
    cor: "text-green",
    titulo: "Valor de mercado por comparáveis",
    nota: "O MVP 2 troca a estimativa manual por um agente que já cruza ImovelWeb, VivaReal e Netimóveis.",
  },
];

function mesAtualPorExtenso(): string {
  return new Date().toLocaleDateString("pt-BR", { month: "long" }).toUpperCase();
}

function FunilCardView({ card, cor }: { card: FunilCardType; cor: string }) {
  const navigate = useNavigate();
  return (
    <div
      onClick={() => navigate(`/imoveis/${card.lote_id}`)}
      className="cursor-pointer rounded-sm border border-border bg-surface p-[11px_12px] hover:border-border3 hover:bg-white"
      style={{ borderLeft: `3px solid ${cor}` }}
    >
      <div className="text-[13px] leading-[1.35]">{card.endereco}</div>
      <div className="mt-1 font-mono text-[10.5px] text-label">{card.cidade}</div>
      <div className="mt-1 flex items-center justify-between">
        <span className="font-mono text-[12px] font-semibold">R$ {Number(card.preco_venda).toLocaleString("pt-BR")}</span>
        {card.desconto_pct && (
          <span className={`font-mono text-[11px] font-semibold ${Number(card.desconto_pct) >= 45 ? "text-green" : ""}`}>
            {formatPercent(card.desconto_pct)}
          </span>
        )}
      </div>
      <div className="mt-2 flex items-center justify-between border-t border-divider pt-2">
        <div className="flex items-center gap-1">
          {CHAVES_RESUMO.map((chave) => (
            <ProcedenciaSquare key={chave} origem={card.resumo_campos.faltando.includes(chave) ? "vazio" : "manual"} />
          ))}
        </div>
        <span className="rounded-pill bg-surface2 px-2 py-[2px] font-mono text-[10px] text-textMuted">
          {card.pilula_estado}
        </span>
      </div>
    </div>
  );
}

export function Funil() {
  const { data, isLoading } = useFunil();

  return (
    <div className="p-[24px_28px_60px]">
      <div className="mb-[18px] flex flex-wrap items-end justify-between gap-6">
        <div>
          <div className="mb-[6px] font-mono text-[10.5px] uppercase tracking-[0.18em] text-label">
            Funil de aprovação · {mesAtualPorExtenso()}
          </div>
          <h1 className="m-0 font-serif text-[30px] font-semibold tracking-[-0.015em]">
            Da fila de triagem até o lance
          </h1>
        </div>
        <div className="flex gap-[26px] text-right">
          <div>
            <div className="font-mono text-[9.5px] uppercase tracking-[0.13em] text-label">Base → aprovados</div>
            <div className="mt-1 font-serif text-[22px] font-semibold">
              {data ? formatPercent(data.base_para_aprovados_pct) : "…"}
            </div>
          </div>
          <div>
            <div className="font-mono text-[9.5px] uppercase tracking-[0.13em] text-label">
              Tempo médio de pesquisa
            </div>
            <div className="mt-1 font-serif text-[22px] font-semibold">
              {data?.tempo_medio_pesquisa_dias ? `${data.tempo_medio_pesquisa_dias.replace(".", ",")} dias` : "—"}
            </div>
          </div>
        </div>
      </div>

      {isLoading && <div className="text-[13px] text-textSoft">Carregando…</div>}

      {data && (
        <div className="grid min-h-[430px] grid-cols-5 gap-[14px] rounded-md border border-border bg-colBg p-3">
          {data.colunas.map((coluna) => {
            const cor = ETAPA_COR[coluna.etapa];
            return (
              <div key={coluna.etapa} className="flex flex-col gap-2">
                <div className="flex items-baseline justify-between">
                  <span className="font-serif text-[14px] font-semibold">{ETAPA_TITULO[coluna.etapa]}</span>
                  <span className="font-mono text-[11px] text-label">{coluna.contagem}</span>
                </div>
                <div className="text-[11.5px] text-label">{coluna.nota}</div>
                <div className="h-[3px] rounded-[2px] bg-track">
                  <div
                    className="h-full rounded-[2px]"
                    style={{ width: `${coluna.barra_pct}%`, backgroundColor: cor }}
                  />
                </div>
                <div className="flex flex-col gap-2">
                  {coluna.cards.map((card) => (
                    <FunilCardView key={card.lote_id} card={card} cor={cor} />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div className="mt-6 grid grid-cols-3 gap-4">
        {CARTOES_EDITORIAIS.map((c) => (
          <div key={c.tag} className="rounded-md border border-border bg-surface p-[14px_16px]">
            <div className={`font-mono text-[10px] uppercase tracking-[0.13em] ${c.cor}`}>{c.tag}</div>
            <div className="mt-1 text-[14.5px] font-semibold">{c.titulo}</div>
            <div className="mt-1 text-[12.5px] text-textSoft">{c.nota}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
