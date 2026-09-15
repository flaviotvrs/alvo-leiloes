import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiGet, apiUpload } from "../client";
import type { ImportacaoDTO } from "../types";

export function useImportacoes() {
  return useQuery({
    queryKey: ["importacoes"],
    queryFn: () => apiGet<ImportacaoDTO[]>("/importacoes"),
  });
}

export function useImportarArquivo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (arquivo: File) => apiUpload<ImportacaoDTO>("/importacoes", arquivo),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["importacoes"] });
      queryClient.invalidateQueries({ queryKey: ["imoveis"] });
      queryClient.invalidateQueries({ queryKey: ["funil"] });
    },
  });
}
