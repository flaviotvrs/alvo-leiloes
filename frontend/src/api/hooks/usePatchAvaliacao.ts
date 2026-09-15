import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiPatch } from "../client";
import type { Checklist } from "../types";
import { fichaQueryKey } from "./useFicha";

interface PatchAvaliacaoInput {
  avaliacaoId: string;
  anotacoes?: string;
  checklist?: Partial<Checklist>;
  tetoLance?: string | null;
  margemDesejadaPct?: string | null;
}

export function usePatchAvaliacao(loteId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ avaliacaoId, anotacoes, checklist, tetoLance, margemDesejadaPct }: PatchAvaliacaoInput) =>
      apiPatch<{ status: string }>(`/avaliacoes/${avaliacaoId}`, {
        anotacoes,
        checklist,
        teto_lance: tetoLance,
        margem_desejada_pct: margemDesejadaPct,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: fichaQueryKey(loteId) });
    },
  });
}
