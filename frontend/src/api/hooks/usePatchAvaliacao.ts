import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiPatch } from "../client";
import type { Checklist } from "../types";
import { fichaQueryKey } from "./useFicha";

interface PatchAvaliacaoInput {
  avaliacaoId: string;
  anotacoes?: string;
  checklist?: Partial<Checklist>;
  tetoLance?: string | null;
}

export function usePatchAvaliacao(loteId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ avaliacaoId, anotacoes, checklist, tetoLance }: PatchAvaliacaoInput) =>
      apiPatch<{ status: string }>(`/avaliacoes/${avaliacaoId}`, {
        anotacoes,
        checklist,
        teto_lance: tetoLance,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: fichaQueryKey(loteId) });
    },
  });
}
