import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiPost } from "../client";
import { fichaQueryKey } from "./useFicha";

export function useDescartar(loteId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ avaliacaoId, motivo }: { avaliacaoId: string; motivo: string }) =>
      apiPost<{ status: string }>(`/avaliacoes/${avaliacaoId}/descartar`, { motivo }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: fichaQueryKey(loteId) });
      queryClient.invalidateQueries({ queryKey: ["funil"] });
      queryClient.invalidateQueries({ queryKey: ["imoveis"] });
    },
  });
}
