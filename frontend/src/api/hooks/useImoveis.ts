import { useQuery } from "@tanstack/react-query";

import { apiGet, buildQuery } from "../client";
import type { ImoveisListResponse } from "../types";

export interface ImoveisFiltros {
  [key: string]: string | number | boolean | string[] | undefined;
  uf?: string;
  cidade?: string;
  bairro?: string;
  preco_min?: number;
  preco_max?: number;
  tipo?: string[];
  financiamento?: "indiferente" | "aceita" | "nao_aceita";
  fgts?: "indiferente" | "aceita" | "nao_aceita";
  desconto_min?: number;
  sem_dados_campo?: boolean;
  /** Filtro só de tela da Triagem, não é enviado ao backend — controla se etapa=descartado
   * entra na lista de etapas buscadas (ver Triagem.tsx). */
  ocultar_descartados?: boolean;
  /** Enviado ao backend — por padrão a Triagem esconde lotes inativos (leilão finalizado/
   * descontinuado); este filtro reexibe. */
  incluir_inativos?: boolean;
  etapa?: string[];
  cursor?: string;
  limit?: number;
}

export function useImoveis(filtros: ImoveisFiltros) {
  return useQuery({
    queryKey: ["imoveis", filtros],
    queryFn: () => apiGet<ImoveisListResponse>(`/imoveis${buildQuery(filtros)}`),
    placeholderData: (dadosAnteriores) => dadosAnteriores,
  });
}
