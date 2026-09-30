import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../client";
import type { ParametroDTO } from "../types";

export function useParametros() {
  return useQuery({
    queryKey: ["parametros"],
    queryFn: () => apiGet<ParametroDTO>("/parametros"),
  });
}
