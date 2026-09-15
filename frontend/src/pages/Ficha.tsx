import { useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { useAceitarSugestao } from "../api/hooks/useAceitarSugestao";
import { useDescartar } from "../api/hooks/useDescartar";
import { useEventos } from "../api/hooks/useEventos";
import { useEventosLote } from "../api/hooks/useEventosLote";
import { useFicha } from "../api/hooks/useFicha";
import { useMoverEtapa } from "../api/hooks/useMoverEtapa";
import { usePatchAvaliacao } from "../api/hooks/usePatchAvaliacao";
import { useSalvarCampo } from "../api/hooks/useSalvarCampo";
import type { CampoDTO, Checklist, Etapa, EventoDTO, GrupoResultado, Linha } from "../api/types";
import { LinhaConta } from "../components/LinhaConta";
import { MoneyValue } from "../components/MoneyValue";
import { PercentValue } from "../components/PercentValue";
import { ProcedenciaChip } from "../components/ProcedenciaChip";
import type { OrigemOuVazio } from "../lib/procedencia";
import { formatArea, formatDateTime, formatMoney } from "../lib/format";

const ETAPAS_ORDEM: Etapa[] = ["nao_avaliado", "pesquisa_campo", "analise_financeira", "decisao", "aprovado_lance"];
const ETAPA_LABEL: Record<Etapa, string> = {
  triagem: "Triagem",
  nao_avaliado: "Não avaliado",
  pesquisa_campo: "Pesquisa de campo",
  analise_financeira: "Análise financeira",
  decisao: "Decisão",
  aprovado_lance: "Aprovado p/ lance",
  descartado: "Descartado",
};
const PROXIMA_ETAPA: Partial<Record<Etapa, Etapa>> = {
  triagem: "nao_avaliado",
  nao_avaliado: "pesquisa_campo",
  pesquisa_campo: "analise_financeira",
  analise_financeira: "decisao",
  decisao: "aprovado_lance",
};

type TipoControle = "money" | "percent" | "select";

interface CampoSpec {
  chave: string;
  rotulo: string;
  hint: string;
  tipo: TipoControle;
  opcoes?: { valor: string; rotulo: string }[];
  comSugestao?: boolean;
}

const CAMPOS_FICHA: CampoSpec[] = [
  {
    chave: "aceita_fgts",
    rotulo: "Aceita FGTS?",
    hint: "Confirmado na página do imóvel ou no edital",
    tipo: "select",
    opcoes: [
      { valor: "nao_verificado", rotulo: "Não verificado" },
      { valor: "aceita", rotulo: "Aceita FGTS" },
      { valor: "nao_aceita", rotulo: "Não aceita" },
    ],
  },
  {
    chave: "valor_mercado",
    rotulo: "Valor real de mercado",
    hint: "Sua estimativa a partir de anúncios da região",
    tipo: "money",
    comSugestao: true,
  },
  { chave: "iptu_atraso", rotulo: "IPTU em atraso", hint: "Consulta na prefeitura ou no edital", tipo: "money" },
  {
    chave: "condominio_atraso",
    rotulo: "Débito de condomínio",
    hint: "Casa isolada normalmente não tem",
    tipo: "money",
  },
  {
    chave: "itbi_aliquota_pct",
    rotulo: "Alíquota de ITBI",
    hint: "Não cadastrada. Enquanto em branco, a conta usa 3% como palpite",
    tipo: "percent",
  },
  {
    chave: "comissao_leiloeiro_pct",
    rotulo: "Comissão do leiloeiro",
    hint: "Está no edital. Em branco, a conta usa 5%",
    tipo: "percent",
  },
  {
    chave: "iptu_mensal",
    rotulo: "IPTU mensal atual",
    hint: "Consulta guiada no site da prefeitura, por nº de inscrição",
    tipo: "money",
  },
  {
    chave: "condominio_mensal",
    rotulo: "Condomínio mensal atual",
    hint: "Confirmar com administradora ou síndico",
    tipo: "money",
  },
  {
    chave: "ocupacao",
    rotulo: "Ocupação",
    hint: "Confirmada em visita ou com vizinhos",
    tipo: "select",
    opcoes: [
      { valor: "nao_verificado", rotulo: "Não verificado" },
      { valor: "desocupado", rotulo: "Desocupado" },
      { valor: "ocupado_mutuario", rotulo: "Ocupado — antigo mutuário" },
      { valor: "ocupado_terceiros", rotulo: "Ocupado — terceiros" },
      { valor: "locado_com_contrato", rotulo: "Locado com contrato" },
    ],
  },
  { chave: "reforma", rotulo: "Reforma estimada", hint: "Orçamento aproximado após a visita", tipo: "money" },
  { chave: "desocupacao", rotulo: "Custo de desocupação", hint: "Acordo amigável ou ação judicial", tipo: "money" },
];

const ROTULO_GRUPO: Record<string, string> = {
  aquisicao: "Aquisição",
  dividas: "Dívidas anteriores assumidas",
  posse: "Recuperação e posse",
  carregamento: "Carregamento · 12 meses",
  venda: "Venda",
};

const CHECKLIST_ITENS: { chave: keyof Checklist; rotulo: string }[] = [
  { chave: "matricula", rotulo: "Matrícula do imóvel obtida no CRI" },
  { chave: "visita", rotulo: "Visita ou foto recente do imóvel" },
  { chave: "iptu", rotulo: "IPTU consultado na prefeitura" },
  { chave: "condominio", rotulo: "Taxa de condomínio confirmada" },
  { chave: "edital", rotulo: "Edital lido por inteiro" },
  { chave: "comparaveis", rotulo: "3 anúncios comparáveis salvos" },
];

function origemDoCampo(campo: CampoDTO | undefined): OrigemOuVazio {
  return campo?.origem ?? "vazio";
}

function CampoLinha({
  spec,
  campo,
  loteId,
  avaliacaoId,
}: {
  spec: CampoSpec;
  campo: CampoDTO | undefined;
  loteId: string;
  avaliacaoId: string;
}) {
  const salvar = useSalvarCampo(loteId);
  const aceitarSugestao = useAceitarSugestao(loteId);
  const [rascunho, setRascunho] = useState(campo?.valor ?? "");
  const timer = useRef<number | undefined>(undefined);

  function agendar(valor: string) {
    setRascunho(valor);
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => {
      salvar.mutate({ avaliacaoId, chave: spec.chave, valor: valor.trim() === "" ? null : valor });
    }, 500);
  }

  function salvarSelect(valor: string) {
    setRascunho(valor);
    salvar.mutate({ avaliacaoId, chave: spec.chave, valor });
  }

  const vazio = !campo;

  return (
    <div className="grid grid-cols-[minmax(170px,236px)_minmax(0,1fr)] gap-[18px] border-b border-divider2 py-[14px]">
      <div>
        <div className="flex items-center gap-2">
          <ProcedenciaChip origem={origemDoCampo(campo)} />
          <span className="text-[13.5px]">{spec.rotulo}</span>
        </div>
        <div className="mt-1 pl-[17px] text-[11.5px] text-labelSoft">{spec.hint}</div>
        {spec.chave === "condominio_atraso" && vazio && (
          <div className="mt-1 pl-[17px] text-[12px] text-red">Sem esse valor a conta abaixo assume zero.</div>
        )}
      </div>
      <div>
        {spec.tipo === "select" ? (
          <select
            className="w-full max-w-[260px] rounded-sm border border-border2 bg-white px-[9px] py-[7px] text-[13px]"
            value={rascunho || "nao_verificado"}
            onChange={(e) => salvarSelect(e.target.value)}
          >
            {spec.opcoes!.map((o) => (
              <option key={o.valor} value={o.valor}>
                {o.rotulo}
              </option>
            ))}
          </select>
        ) : (
          <div className="flex items-center gap-2">
            {spec.tipo === "money" && <span className="text-[13px] text-labelSoft">R$</span>}
            <input
              className={`rounded-sm border px-[9px] py-[7px] text-right text-[13px] ${
                vazio ? "border-border3 bg-surface4" : "border-border2 bg-white"
              } ${spec.tipo === "money" ? "w-[130px]" : "w-[90px]"}`}
              value={rascunho}
              onChange={(e) => agendar(e.target.value)}
              placeholder="0"
            />
            {spec.tipo === "percent" && <span className="text-[13px] text-labelSoft">%</span>}
          </div>
        )}

        {spec.comSugestao && campo?.valor && campo.sugestao_valor && (
          <div className="mt-2 flex items-center gap-2">
            <span className="text-[12px] text-amber">
              Automação futura sugeriria {formatMoney(campo.sugestao_valor)}
            </span>
            <button
              type="button"
              onClick={() => aceitarSugestao.mutate({ avaliacaoId, chave: spec.chave })}
              className="rounded-sm border border-amberBorder bg-amberBg px-2 py-1 text-[11.5px] text-amber"
            >
              Usar valor da automação
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function corSubtotalGrupo(grupo: GrupoResultado): string {
  const valor = Number(grupo.subtotal);
  if (grupo.grupo === "dividas") return valor > 0 ? "text-red" : "text-labelSoft";
  if (grupo.grupo === "carregamento") return valor > 0 ? "text-amber" : "text-ink";
  if (grupo.grupo === "venda") return "text-green";
  return "text-ink";
}

export function Ficha() {
  const { loteId } = useParams<{ loteId: string }>();
  const navigate = useNavigate();
  const { data: ficha, isLoading } = useFicha(loteId);
  const { data: eventosAvaliacao } = useEventos(ficha?.avaliacao.id);
  const { data: eventosLote } = useEventosLote(loteId);
  const eventos = [...(eventosAvaliacao ?? []), ...(eventosLote ?? [])].sort(
    (a, b) => new Date(b.criado_em).getTime() - new Date(a.criado_em).getTime(),
  );
  const moverEtapa = useMoverEtapa(loteId ?? "");
  const descartar = useDescartar(loteId ?? "");
  const patchAvaliacao = usePatchAvaliacao(loteId ?? "");
  const [contaAberta, setContaAberta] = useState(true);
  const [anotacoes, setAnotacoes] = useState<string | undefined>(undefined);
  const anotacoesTimer = useRef<number | undefined>(undefined);

  if (isLoading || !ficha) {
    return <div className="p-[22px_28px_60px] text-[13px] text-textSoft">Carregando…</div>;
  }

  const { imovel, lote, avaliacao, campos, resultado_calculo: resultado } = ficha;
  const totalCampos = CAMPOS_FICHA.length;
  const preenchidos = CAMPOS_FICHA.filter((c) => campos[c.chave]).length;
  const indiceEtapa = ETAPAS_ORDEM.indexOf(avaliacao.etapa);
  const proximaEtapa = PROXIMA_ETAPA[avaliacao.etapa];

  function agendarAnotacoes(valor: string) {
    setAnotacoes(valor);
    window.clearTimeout(anotacoesTimer.current);
    anotacoesTimer.current = window.setTimeout(() => {
      patchAvaliacao.mutate({ avaliacaoId: avaliacao.id, anotacoes: valor });
    }, 500);
  }

  function avancar() {
    if (!proximaEtapa) return;
    moverEtapa.mutate({ avaliacaoId: avaliacao.id, etapa: proximaEtapa });
  }

  function descartarAvaliacao() {
    const motivo = window.prompt("Motivo do descarte:");
    if (!motivo) return;
    descartar.mutate({ avaliacaoId: avaliacao.id, motivo }, { onSuccess: () => navigate("/triagem") });
  }

  const corMargem =
    resultado.veredito === "aprovado" ? "bg-greenBg" : resultado.veredito === "reprovado" ? "bg-redBg" : "bg-surface2";
  const notaMargem =
    resultado.veredito === "aprovado"
      ? "Acima do piso de 20% — segue no funil."
      : resultado.veredito === "reprovado"
        ? "Abaixo do piso de 20% — a regra é não participar."
        : "Preencha o valor de revenda para ver a margem.";

  return (
    <div className="p-[22px_28px_60px]">
      <div className="mb-4 font-mono text-[11px]">
        <Link to="/triagem" className="font-serif text-green">
          ← Triagem
        </Link>{" "}
        <span className="text-labelSoft">/</span> IMÓVEL {lote.codigo_externo}
      </div>

      <div className="grid grid-cols-[minmax(0,1fr)_352px] items-start gap-5">
        <div className="flex flex-col gap-5">
          {/* Bloco A — dados do imóvel */}
          <div className="overflow-hidden rounded-md border border-border bg-surface">
            <div className="flex items-center justify-between bg-surface2 px-5 py-[10px]">
              <span className="font-mono text-[9.5px] uppercase tracking-[0.13em] text-label">
                Dados do imóvel · somente leitura
              </span>
              <span className="font-mono text-[10.5px] text-labelSoft">Importado da planilha da Caixa</span>
            </div>
            {!lote.ativo && (
              <div className="border-b border-amberBorder bg-amberBg px-5 py-[9px] font-mono text-[11px] text-amber">
                Leilão finalizado/descontinuado — este imóvel saiu da planilha de origem. Os dados abaixo podem
                estar desatualizados; a análise já feita continua preservada.
              </div>
            )}
            <div className="p-[18px_22px]">
              <h1 className="m-0 font-serif text-[26px] font-semibold tracking-[-0.015em]">{imovel.endereco}</h1>
              <div className="mt-1 text-[13.5px] text-textMuted">
                {imovel.bairro ? `${imovel.bairro}, ` : ""}
                {imovel.cidade} · {imovel.uf}
              </div>
              {imovel.descricao_oficial && (
                <div className="mt-3 border-t border-dashed border-[#E0DCD2] pt-3 text-[13px] text-textSoft">
                  {imovel.descricao_oficial}
                </div>
              )}

              <div className="mt-4 grid grid-cols-4 gap-px overflow-hidden rounded-sm bg-border">
                {[
                  { rotulo: "Preço de venda", valor: formatMoney(lote.preco_venda), hint: "campo Preço" },
                  { rotulo: "Valor de avaliação", valor: formatMoney(lote.valor_avaliacao), hint: "calculado pela Caixa" },
                  {
                    rotulo: "Desconto",
                    valor: lote.desconto_pct ? `${Number(lote.desconto_pct).toFixed(1).replace(".", ",")}%` : "—",
                    hint: "importado da planilha",
                    destaque: true,
                  },
                  { rotulo: "Área privativa", valor: formatArea(imovel.area_privativa_m2), hint: "extraído da descrição" },
                ].map((m) => (
                  <div key={m.rotulo} className="bg-surface p-3">
                    <div className="font-mono text-[9.5px] uppercase tracking-[0.13em] text-label">{m.rotulo}</div>
                    <div className={`mt-1 font-mono text-[19px] font-semibold ${m.destaque ? "text-green" : ""}`}>
                      {m.valor}
                    </div>
                    <div className="mt-1 text-[11.5px] text-labelSoft">{m.hint}</div>
                  </div>
                ))}
              </div>

              <div className="mt-4 flex flex-wrap items-center gap-2">
                <span className="rounded-pill border border-dividerDash px-3 py-1 text-[12px] text-textMuted">
                  {lote.modalidade ?? "Modalidade não informada"}
                </span>
                <span className="rounded-pill border border-dividerDash px-3 py-1 text-[12px] text-textMuted">
                  {lote.aceita_financiamento ? "Aceita financiamento" : "Não aceita financiamento"}
                </span>
                {lote.url_fonte && (
                  <a href={lote.url_fonte} target="_blank" rel="noreferrer" className="text-[12.5px]">
                    Abrir no site da Caixa ↗
                  </a>
                )}
              </div>
            </div>
          </div>

          {/* Bloco B — dados de campo */}
          <div className="overflow-hidden rounded-md border border-border bg-surface">
            <div className="flex items-center justify-between bg-surface2 px-5 py-[10px]">
              <span className="font-mono text-[9.5px] uppercase tracking-[0.13em] text-label">
                Dados de campo · você preenche
              </span>
              <span className={`font-mono text-[10.5px] ${preenchidos === totalCampos ? "text-green" : "text-amber"}`}>
                {preenchidos}/{totalCampos} campos preenchidos
              </span>
            </div>
            <div className="px-5">
              {CAMPOS_FICHA.map((spec) => (
                <CampoLinha
                  key={`${spec.chave}-${campos[spec.chave]?.preenchido_em ?? "vazio"}`}
                  spec={spec}
                  campo={campos[spec.chave]}
                  loteId={loteId!}
                  avaliacaoId={avaliacao.id}
                />
              ))}
              <div className="py-[14px]">
                <div className="mb-2 font-mono text-[10px] uppercase tracking-[0.16em] text-label">
                  Anotações da visita
                </div>
                <textarea
                  className="min-h-[74px] w-full resize-y rounded-sm border border-border2 p-2 text-[13px] leading-[1.5]"
                  placeholder="O que você viu no local, com quem falou, o que ainda falta confirmar."
                  value={anotacoes ?? avaliacao.anotacoes}
                  onChange={(e) => agendarAnotacoes(e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* Bloco C — conta do negócio */}
          <div className="overflow-hidden rounded-md border border-border bg-surface">
            <div className="flex items-center justify-between bg-surface2 px-5 py-[10px]">
              <span className="font-mono text-[9.5px] uppercase tracking-[0.13em] text-label">Conta do negócio</span>
              <span className="text-[12px] text-labelSoft">cenário à vista · revenda em 12 meses</span>
            </div>
            <div className="grid grid-cols-[repeat(auto-fit,minmax(280px,1fr))] gap-[26px] p-[18px_22px]">
              <div>
                {[
                  { rotulo: "Investimento total até a revenda", valor: resultado.investimento, peso: "font-semibold" },
                  { rotulo: "Revenda estimada", valor: campos.valor_mercado?.valor ?? null },
                  { rotulo: "Comissão do corretor", valor: resultado.comissao_corretor ? `-${resultado.comissao_corretor}` : null },
                  { rotulo: "IR sobre ganho de capital", valor: resultado.ir ? `-${resultado.ir}` : null },
                ].map((linha) => (
                  <div
                    key={linha.rotulo}
                    className="flex items-center justify-between border-b border-dashed border-dividerDash py-[7px]"
                  >
                    <span className="text-[13px]">{linha.rotulo}</span>
                    {linha.valor === null ? (
                      <span className="font-mono text-[13px] text-labelSoft">em branco</span>
                    ) : (
                      <MoneyValue value={linha.valor} className={`text-[13px] ${linha.peso ?? ""}`} />
                    )}
                  </div>
                ))}
                <div className="flex items-center justify-between pt-[10px]">
                  <span className="text-[13.5px] font-semibold">Lucro líquido</span>
                  <MoneyValue
                    value={resultado.lucro}
                    className={`text-[17px] font-semibold ${
                      resultado.lucro !== null && Number(resultado.lucro) < 0 ? "text-red" : "text-green"
                    }`}
                  />
                </div>
              </div>

              <div className={`rounded-sm p-[16px_18px] ${corMargem}`}>
                <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-label">
                  Margem sobre o investimento
                </div>
                <PercentValue value={resultado.margem_investimento_pct} withSign className="text-[30px] font-semibold" />
                <div className="mt-1 text-[12.5px]">{notaMargem}</div>
                {resultado.margem_revenda_pct && (
                  <div className="mt-3 border-t border-black/10 pt-2 font-mono text-[10.5px]">
                    equivale a {resultado.margem_revenda_pct.replace(".", ",")}% sobre a revenda
                  </div>
                )}
              </div>
            </div>

            <div className="px-[22px] pb-[18px]">
              <button
                type="button"
                onClick={() => setContaAberta((v) => !v)}
                className="w-full rounded-sm border border-border2 py-[9px] font-mono text-[10.5px] uppercase text-ink3 hover:bg-surface2"
              >
                {contaAberta ? "Fechar a conta detalhada ▴" : "Abrir a conta detalhada ▾"}
              </button>

              {contaAberta && (
                <div className="mt-4 flex flex-col gap-5">
                  {resultado.grupos.map((grupo) => (
                    <div key={grupo.grupo}>
                      <div className="mb-1 flex items-center justify-between">
                        <span className={`font-mono text-[9.5px] uppercase tracking-[0.13em] ${corSubtotalGrupo(grupo)}`}>
                          {ROTULO_GRUPO[grupo.grupo]}
                        </span>
                        <MoneyValue value={grupo.subtotal} className={`text-[12px] font-semibold ${corSubtotalGrupo(grupo)}`} />
                      </div>
                      {grupo.linhas.map((linha: Linha) => (
                        <LinhaConta key={linha.chave} linha={linha} />
                      ))}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Coluna direita */}
        <div className="sticky top-[76px] flex flex-col gap-5">
          <div className="rounded-md bg-ink p-[18px_20px] text-onDark">
            <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-onDark4">Etapa atual</div>
            <div className="mt-1 font-serif text-[19px] font-semibold">{ETAPA_LABEL[avaliacao.etapa]}</div>
            <div className="mt-1 text-[12.5px] text-onDark3">desde {formatDateTime(avaliacao.etapa_desde)}</div>
            <div className="mt-3 flex gap-[3px]">
              {ETAPAS_ORDEM.map((etapa, i) => (
                <div
                  key={etapa}
                  className={`h-1 flex-1 rounded-[2px] ${i <= indiceEtapa ? "bg-onDark" : "bg-onDarkBorder"}`}
                />
              ))}
            </div>
            {proximaEtapa && (
              <button
                type="button"
                onClick={avancar}
                className={`mt-4 w-full rounded-sm py-[9px] text-[13px] font-semibold ${
                  preenchidos === totalCampos ? "bg-green text-white" : "bg-[#6E6A5E] text-white"
                }`}
              >
                {preenchidos === totalCampos ? "Enviar para decisão" : "Enviar mesmo com lacunas"}
              </button>
            )}
            <button
              type="button"
              onClick={descartarAvaliacao}
              className="mt-2 w-full rounded-sm border border-onDarkBorder py-[9px] text-[13px] text-onDark2"
            >
              Descartar
            </button>
            {preenchidos < totalCampos && (
              <div className="mt-2 text-[12px] text-onDark4">
                {totalCampos - preenchidos} campo(s) em branco. Dá para avançar, mas fica registrado quem decidiu sem o
                dado.
              </div>
            )}
          </div>

          <div className="rounded-md border border-border bg-surface p-[14px_16px]">
            <div className="mb-2 flex items-center justify-between">
              <span className="font-mono text-[9.5px] uppercase tracking-[0.13em] text-label">Checklist de campo</span>
              <span className="font-mono text-[11px] text-label">
                {CHECKLIST_ITENS.filter((i) => avaliacao.checklist[i.chave]).length}/{CHECKLIST_ITENS.length}
              </span>
            </div>
            {CHECKLIST_ITENS.map((item) => {
              const marcado = avaliacao.checklist[item.chave];
              return (
                <button
                  key={item.chave}
                  type="button"
                  onClick={() =>
                    patchAvaliacao.mutate({ avaliacaoId: avaliacao.id, checklist: { [item.chave]: !marcado } })
                  }
                  className="flex w-full items-center gap-2 rounded-sm px-1 py-[6px] text-left hover:bg-surface2"
                >
                  <span
                    className={`grid h-[15px] w-[15px] flex-shrink-0 place-items-center rounded-sm border-[1.5px] text-[10px] text-white ${
                      marcado ? "border-green bg-green" : "border-border2 bg-white"
                    }`}
                  >
                    {marcado ? "✓" : ""}
                  </span>
                  <span className={`text-[13px] ${marcado ? "text-textSoft line-through" : ""}`}>{item.rotulo}</span>
                </button>
              );
            })}
          </div>

          <div className="rounded-md border border-border bg-surface p-[14px_16px]">
            <div className="mb-2 font-mono text-[9.5px] uppercase tracking-[0.13em] text-label">
              Histórico do registro
            </div>
            <div className="flex flex-col gap-3">
              {(eventos ?? []).map((evento) => (
                <div key={evento.id} className="flex items-start gap-2">
                  <span
                    className={`grid h-6 w-6 flex-shrink-0 place-items-center rounded-full font-mono text-[9.5px] ${
                      evento.ator_id ? "bg-greenBg text-green" : "bg-dividerDash text-textMuted"
                    }`}
                  >
                    {evento.ator_id ? "FL" : "·"}
                  </span>
                  <div>
                    <div className="text-[12.5px]">{textoEvento(evento)}</div>
                    <div className="font-mono text-[10.5px] text-labelSoft">{formatDateTime(evento.criado_em)}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function textoEvento(evento: EventoDTO): string {
  const payload = evento.payload;
  switch (evento.tipo) {
    case "importacao":
      switch (payload.acao) {
        case "criado":
          return "Criado a partir da planilha da Caixa.";
        case "atualizado": {
          const mudancas = (payload.mudancas as Record<string, { de: unknown; para: unknown }>) ?? {};
          const campos = Object.keys(mudancas).join(", ");
          return `Atualizado pela importação (${campos || "sem detalhe"}).`;
        }
        case "inativado":
          return "Inativado: saiu da planilha da Caixa nesta carga.";
        case "reativado":
          return "Reativado: voltou a aparecer na planilha da Caixa.";
        default:
          return "Importado da planilha da Caixa.";
      }
    case "campo_alterado":
      return `Campo "${payload.chave}" alterado de "${payload.de ?? "vazio"}" para "${payload.para ?? "vazio"}".`;
    case "etapa_alterada":
      return `Etapa alterada de "${ETAPA_LABEL[payload.de as Etapa] ?? payload.de}" para "${
        ETAPA_LABEL[payload.para as Etapa] ?? payload.para
      }".`;
    case "descarte":
      return `Descartado: ${payload.motivo}`;
    case "sugestao_aceita":
      return `Sugestão de automação aceita para "${payload.chave}".`;
    default:
      return "Cálculo recalculado.";
  }
}
