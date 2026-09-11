import { formatMoney } from "../lib/format";
import type { Linha } from "../api/types";

/** Uma linha da conta detalhada (README "Bloco C — Conta do negócio", detalhe expansível).
 * Quando `assumido`, tudo fica em âmbar e o hint (`fonte`) diz o que fazer para confirmar —
 * é a regra "palpite nunca se disfarça de fato" do produto. */
export function LinhaConta({ linha }: { linha: Linha }) {
  const cor = linha.assumido ? "text-amber" : "text-ink";
  const corHint = linha.assumido ? "text-amber" : "text-labelSoft";

  return (
    <div className="grid grid-cols-[minmax(0,1fr)_auto] items-baseline gap-[18px] py-[3px]">
      <div>
        <div className={`text-[13px] ${cor}`}>{linha.rotulo}</div>
        <div className={`text-[11.5px] ${corHint}`}>{linha.fonte}</div>
      </div>
      <div className={`font-mono text-[13px] ${cor}`}>
        {linha.valor === null ? <span className="text-labelSoft">em branco</span> : formatMoney(linha.valor)}
      </div>
    </div>
  );
}
