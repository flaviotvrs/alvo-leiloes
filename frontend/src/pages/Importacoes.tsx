import { useRef, useState } from "react";

import { useImportacoes, useImportarArquivo } from "../api/hooks/useImportacoes";
import type { ImportacaoDTO } from "../api/types";
import { formatDate, formatDateTime } from "../lib/format";

function badgeStatus(importacao: ImportacaoDTO): { texto: string; classe: string } {
  if (importacao.status === "processando") {
    return { texto: "Processando", classe: "border-border2 bg-surface2 text-textMuted" };
  }
  if (importacao.status === "falhou") {
    return { texto: "Falhou", classe: "border-redBg2 bg-redBg text-red" };
  }
  if (importacao.erros.length > 0) {
    return { texto: `Concluída com ${importacao.erros.length} erro(s)`, classe: "border-amberBorder bg-amberBg text-amber" };
  }
  return { texto: "Concluída", classe: "border-greenBorder bg-greenBg text-green" };
}

export function Importacoes() {
  const { data: importacoes, isLoading } = useImportacoes();
  const importar = useImportarArquivo();
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [linhaExpandida, setLinhaExpandida] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function enviar() {
    if (!arquivo) return;
    importar.mutate(arquivo, {
      onSuccess: () => {
        setArquivo(null);
        if (inputRef.current) inputRef.current.value = "";
      },
    });
  }

  return (
    <div className="p-[24px_28px_60px]">
      <div className="mb-[18px]">
        <div className="mb-[6px] font-mono text-[10.5px] uppercase tracking-[0.18em] text-label">
          Importação de dados
        </div>
        <h1 className="m-0 font-serif text-[30px] font-semibold tracking-[-0.015em]">
          Planilha da Caixa e histórico de cargas
        </h1>
      </div>

      <div className="mb-6 flex items-center gap-3 rounded-md border border-border bg-surface p-[16px_18px]">
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          onChange={(e) => setArquivo(e.target.files?.[0] ?? null)}
          className="flex-1 text-[13px] text-textMuted file:mr-3 file:rounded-sm file:border file:border-border2 file:bg-surface2 file:px-3 file:py-[6px] file:font-serif file:text-[12.5px] file:text-ink3"
        />
        <button
          type="button"
          disabled={!arquivo || importar.isPending}
          onClick={enviar}
          className="rounded-sm border border-greenBorder bg-greenBg px-4 py-[7px] font-serif text-[13px] text-green disabled:cursor-not-allowed disabled:opacity-40"
        >
          {importar.isPending ? "Importando…" : "Importar"}
        </button>
        {importar.isError && (
          <span className="font-mono text-[11.5px] text-red">
            {importar.error instanceof Error ? importar.error.message : "Falha ao importar"}
          </span>
        )}
      </div>

      <div className="overflow-hidden rounded-md border border-border bg-surface">
        <div className="grid grid-cols-[1.8fr_1fr_0.8fr_0.9fr_0.8fr_0.8fr_1.3fr] gap-[14px] bg-surface2 px-[18px] py-2 font-mono text-[9.5px] uppercase tracking-[0.13em] text-label">
          <div>Arquivo</div>
          <div>Geração</div>
          <div className="text-right">Adicionados</div>
          <div className="text-right">Modificados</div>
          <div className="text-right">Inativados</div>
          <div className="text-right">Reativados</div>
          <div>Status</div>
        </div>

        {isLoading && <div className="p-[38px] text-center text-[13px] text-textSoft">Carregando…</div>}

        {!isLoading && importacoes?.length === 0 && (
          <div className="p-[38px] text-center">
            <div className="text-[13px] text-textSoft">Nenhuma importação ainda.</div>
            <div className="mt-1 text-[11.5px] text-labelSoft">Envie a planilha (CSV) da Caixa acima.</div>
          </div>
        )}

        {importacoes?.map((importacao) => {
          const badge = badgeStatus(importacao);
          const expandida = linhaExpandida === importacao.id;
          const temErros = importacao.erros.length > 0;
          return (
            <div key={importacao.id} className="border-t border-divider">
              <div
                onClick={() => temErros && setLinhaExpandida(expandida ? null : importacao.id)}
                className={`grid grid-cols-[1.8fr_1fr_0.8fr_0.9fr_0.8fr_0.8fr_1.3fr] items-center gap-[14px] px-[18px] py-[13px] ${
                  temErros ? "cursor-pointer hover:bg-surface3" : ""
                }`}
              >
                <div className="min-w-0">
                  <div className="truncate text-[13.5px]">{importacao.arquivo_nome ?? "—"}</div>
                  <div className="font-mono text-[10.5px] text-labelSoft">{formatDateTime(importacao.iniciada_em)}</div>
                </div>
                <div className="text-[13px] text-textMuted">{formatDate(importacao.arquivo_gerado_em)}</div>
                <div className="text-right font-mono text-[13px] text-green">{importacao.criados}</div>
                <div className="text-right font-mono text-[13px] text-ink">{importacao.atualizados}</div>
                <div className="text-right font-mono text-[13px] text-red">{importacao.inativados}</div>
                <div className="text-right font-mono text-[13px] text-textMuted">{importacao.reativados}</div>
                <div>
                  <span className={`rounded-pill border px-2 py-[3px] font-mono text-[10.5px] ${badge.classe}`}>
                    {badge.texto}
                  </span>
                  {temErros && (
                    <span className="ml-2 font-mono text-[10.5px] text-labelSoft">
                      {expandida ? "ocultar detalhe ▲" : "ver detalhe ▼"}
                    </span>
                  )}
                </div>
              </div>
              {expandida && (
                <div className="border-t border-dividerDash bg-surface2 px-[18px] py-3">
                  <div className="mb-2 font-mono text-[9.5px] uppercase tracking-[0.13em] text-label">
                    Linhas com erro
                  </div>
                  <div className="flex flex-col gap-1">
                    {importacao.erros.map((erro, i) => (
                      <div key={i} className="font-mono text-[11.5px] text-textMuted">
                        <span className="text-red">{erro.codigo_externo}</span> — {erro.erro}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
