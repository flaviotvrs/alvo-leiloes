import { useQueries } from "@tanstack/react-query";

import { apiGet, buildQuery } from "../client";
import type { ImoveisListResponse } from "../types";

/** GET /imoveis não tem endpoint de KPI dedicado — reaproveita o `total` (já filtrado, não
 * só a página) com 4 requisições leves (`limit=1`) em paralelo. Ver plano: decisão
 * deliberada para não tocar o backend de novo por 4 números decorativos. */
function contagem(chave: string, filtros: Record<string, string | number | boolean | string[]>) {
  return {
    queryKey: ["imoveis", "kpi", chave],
    queryFn: () => apiGet<ImoveisListResponse>(`/imoveis${buildQuery({ ...filtros, limit: 1 })}`),
  };
}

export function useTriagemKpis() {
  const [total, naoAvaliados, semDados, prontos, desconto40] = useQueries({
    queries: [
      contagem("total", {}),
      contagem("nao_avaliado", { etapa: "nao_avaliado" }),
      contagem("sem_dados", { sem_dados_campo: true }),
      contagem("prontos", { etapa: ["decisao", "aprovado_lance"] }),
      contagem("desconto40", { desconto_min: 40 }),
    ],
  });

  const carregando = [total, naoAvaliados, semDados, prontos, desconto40].some((r) => r.isLoading);

  return {
    carregando,
    naoAvaliados: naoAvaliados.data?.total,
    comDadosDeCampo:
      total.data !== undefined && semDados.data !== undefined
        ? total.data.total - semDados.data.total
        : undefined,
    prontosParaDecisao: prontos.data?.total,
    descontoMaiorIgual40: desconto40.data?.total,
    totalGeral: total.data?.total,
  };
}
