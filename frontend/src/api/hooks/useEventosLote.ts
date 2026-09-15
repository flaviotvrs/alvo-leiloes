import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../client";
import type { EventoDTO } from "../types";

export function useEventosLote(loteId: string | undefined) {
  return useQuery({
    queryKey: ["eventos-lote", loteId],
    queryFn: () => apiGet<EventoDTO[]>(`/imoveis/${loteId}/eventos`),
    enabled: Boolean(loteId),
  });
}
