import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../client";
import type { FichaResponse } from "../types";

export function fichaQueryKey(loteId: string) {
  return ["ficha", loteId];
}

export function useFicha(loteId: string | undefined) {
  return useQuery({
    queryKey: fichaQueryKey(loteId ?? ""),
    queryFn: () => apiGet<FichaResponse>(`/imoveis/${loteId}`),
    enabled: Boolean(loteId),
  });
}
