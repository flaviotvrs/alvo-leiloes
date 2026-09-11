import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../client";
import type { FacetasResponse } from "../types";

export function useFacetas() {
  return useQuery({
    queryKey: ["imoveis", "facetas"],
    queryFn: () => apiGet<FacetasResponse>("/imoveis/facetas"),
    staleTime: 5 * 60 * 1000,
  });
}
