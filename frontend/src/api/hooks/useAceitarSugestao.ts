import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiPost } from "../client";
import type { Resultado } from "../types";
import { fichaQueryKey } from "./useFicha";

export function useAceitarSugestao(loteId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ avaliacaoId, chave }: { avaliacaoId: string; chave: string }) =>
      apiPost<Resultado>(`/avaliacoes/${avaliacaoId}/campos/${chave}/aceitar-sugestao`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: fichaQueryKey(loteId) });
    },
  });
}
