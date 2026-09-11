import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../client";
import type { FunilResponse } from "../types";

export function useFunil() {
  return useQuery({
    queryKey: ["funil"],
    queryFn: () => apiGet<FunilResponse>("/funil"),
  });
}
