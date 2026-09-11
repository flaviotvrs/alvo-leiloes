import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../client";
import type { EventoDTO } from "../types";

export function useEventos(avaliacaoId: string | undefined) {
  return useQuery({
    queryKey: ["eventos", avaliacaoId],
    queryFn: () => apiGet<EventoDTO[]>(`/avaliacoes/${avaliacaoId}/eventos`),
    enabled: Boolean(avaliacaoId),
  });
}
