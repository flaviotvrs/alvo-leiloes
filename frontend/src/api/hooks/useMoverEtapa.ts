import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiPost } from "../client";
import type { Etapa, Resultado } from "../types";
import { fichaQueryKey } from "./useFicha";

export function useMoverEtapa(loteId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ avaliacaoId, etapa, motivo }: { avaliacaoId: string; etapa: Etapa; motivo?: string }) =>
      apiPost<Resultado>(`/avaliacoes/${avaliacaoId}/etapa`, { etapa, motivo }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: fichaQueryKey(loteId) });
      queryClient.invalidateQueries({ queryKey: ["funil"] });
      queryClient.invalidateQueries({ queryKey: ["imoveis"] });
    },
  });
}
