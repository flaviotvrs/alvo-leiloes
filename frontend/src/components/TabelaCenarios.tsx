import type { ReactNode } from "react";

import type { GrupoResultado, Linha, Resultado, Veredito } from "../api/types";
import { formatMoney, formatPercent } from "../lib/format";

const ROTULO_GRUPO: Record<string, string> = {
  aquisicao: "Aquisição",
  dividas: "Dívidas anteriores assumidas",
  posse: "Recuperação e posse",
  carregamento: "Carregamento · 12 meses",
  venda: "Venda",
};

const ROTULO_VEREDITO: Record<Veredito, string> = {
  aprovado: "aprovado",
  reprovado: "reprovado",
  incompleto: "incompleto",
};

const COR_VEREDITO: Record<Veredito, string> = {
  aprovado: "text-green",
  reprovado: "text-red",
  incompleto: "text-labelSoft",
};

function corSubtotalGrupo(grupo: GrupoResultado): string {
  const valor = Number(grupo.subtotal);
  if (grupo.grupo === "dividas") return valor > 0 ? "text-red" : "text-labelSoft";
  if (grupo.grupo === "carregamento") return valor > 0 ? "text-amber" : "text-ink";
  if (grupo.grupo === "venda") return "text-green";
  return "text-ink";
}

export interface Cenario {
  titulo: string;
  /** Valor do arremate do cenário — fixo ou um input editável. */
  cabecalho: ReactNode;
  /** `null` quando o cenário não tem lance (sem teto digitado, sem lance máximo viável). */
  resultado: Resultado | null;
}

const GRID = "grid grid-cols-[minmax(0,1fr)_repeat(3,minmax(0,130px))] items-baseline gap-x-[14px]";

function Vazio() {
  return <span className="text-labelSoft">—</span>;
}

/** Conta do negócio lado a lado para três arremates (README "Bloco C — Conta do negócio"):
 * mínimo do leiloeiro, meu lance e máximo sugerido. O motor devolve sempre as mesmas linhas
 * (mesmas `chave`s), então as colunas são casadas por grupo e chave. A 1ª coluna usa a conta
 * `base` (sempre presente) para rótulos e hints. */
export function TabelaCenarios({
  base,
  cenarios,
  aberta,
}: {
  base: Resultado;
  cenarios: Cenario[];
  aberta: boolean;
}) {
  function grupoDe(resultado: Resultado | null, grupo: string) {
    return resultado?.grupos.find((g) => g.grupo === grupo);
  }

  function linhaDe(resultado: Resultado | null, grupo: string, chave: string): Linha | undefined {
    return grupoDe(resultado, grupo)?.linhas.find((l) => l.chave === chave);
  }

  const totais: { rotulo: string; celula: (r: Resultado) => ReactNode }[] = [
    {
      rotulo: "Investimento total até a revenda",
      celula: (r) => <span className="font-semibold">{formatMoney(r.investimento)}</span>,
    },
    {
      rotulo: "Lucro líquido",
      celula: (r) =>
        r.lucro === null ? (
          <span className="text-labelSoft">em branco</span>
        ) : (
          <span className={`font-semibold ${Number(r.lucro) < 0 ? "text-red" : "text-green"}`}>
            {formatMoney(r.lucro)}
          </span>
        ),
    },
    {
      rotulo: "Margem sobre o investimento",
      celula: (r) => (
        <span className={`font-semibold ${COR_VEREDITO[r.veredito]}`}>
          {formatPercent(r.margem_investimento_pct, { withSign: true })}
        </span>
      ),
    },
    {
      rotulo: "Veredito",
      celula: (r) => <span className={COR_VEREDITO[r.veredito]}>{ROTULO_VEREDITO[r.veredito]}</span>,
    },
  ];

  return (
    <div>
      <div className={`${GRID} border-b border-border pb-[10px]`}>
        <div />
        {cenarios.map((cenario) => (
          <div key={cenario.titulo} className="text-right">
            <div className="font-mono text-[9.5px] uppercase tracking-[0.13em] text-label">{cenario.titulo}</div>
            <div className="mt-1">{cenario.cabecalho}</div>
          </div>
        ))}
      </div>

      {aberta && (
        <div className="mt-3 flex flex-col gap-5">
          {base.grupos.map((grupo) => (
            <div key={grupo.grupo}>
              <div className={`${GRID} mb-1`}>
                <span className={`font-mono text-[9.5px] uppercase tracking-[0.13em] ${corSubtotalGrupo(grupo)}`}>
                  {ROTULO_GRUPO[grupo.grupo]}
                </span>
                {cenarios.map((cenario) => {
                  const g = grupoDe(cenario.resultado, grupo.grupo);
                  return (
                    <span key={cenario.titulo} className="text-right font-mono text-[12px] font-semibold">
                      {g ? <span className={corSubtotalGrupo(g)}>{formatMoney(g.subtotal)}</span> : <Vazio />}
                    </span>
                  );
                })}
              </div>
              {grupo.linhas.map((linha) => (
                <div key={linha.chave} className={`${GRID} py-[3px]`}>
                  <div>
                    <div className={`text-[13px] ${linha.assumido ? "text-amber" : "text-ink"}`}>{linha.rotulo}</div>
                    <div className={`text-[11.5px] ${linha.assumido ? "text-amber" : "text-labelSoft"}`}>
                      {linha.fonte}
                    </div>
                  </div>
                  {cenarios.map((cenario) => {
                    const l = linhaDe(cenario.resultado, grupo.grupo, linha.chave);
                    return (
                      <div
                        key={cenario.titulo}
                        className={`text-right font-mono text-[13px] ${l?.assumido ? "text-amber" : "text-ink"}`}
                      >
                        {!cenario.resultado ? (
                          <Vazio />
                        ) : !l || l.valor === null ? (
                          <span className="text-labelSoft">em branco</span>
                        ) : (
                          formatMoney(l.valor)
                        )}
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      <div className="mt-4 border-t border-border pt-2">
        {totais.map((total) => (
          <div key={total.rotulo} className={`${GRID} border-b border-dashed border-dividerDash py-[7px] last:border-b-0`}>
            <span className="text-[13px]">{total.rotulo}</span>
            {cenarios.map((cenario) => (
              <span key={cenario.titulo} className="text-right font-mono text-[13px]">
                {cenario.resultado ? total.celula(cenario.resultado) : <Vazio />}
              </span>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
