import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiPatch } from "../client";
import type { FichaResponse, Resultado } from "../types";
import { fichaQueryKey } from "./useFicha";

interface SalvarCampoInput {
  avaliacaoId: string;
  chave: string;
  valor: string | null;
  fonteDeclarada?: string;
}

export function useSalvarCampo(loteId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ avaliacaoId, chave, valor, fonteDeclarada }: SalvarCampoInput) =>
      apiPatch<Resultado>(`/avaliacoes/${avaliacaoId}/campos/${chave}`, {
        valor,
        fonte_declarada: fonteDeclarada ?? null,
      }),
    onSuccess: (resultado) => {
      // atualização otimista da conta (feedback instantâneo); os campos (procedência,
      // preenchido_em) ficam consistentes no próximo refetch abaixo.
      queryClient.setQueryData<FichaResponse>(fichaQueryKey(loteId), (anterior) =>
        anterior ? { ...anterior, resultado_calculo: resultado } : anterior,
      );
      queryClient.invalidateQueries({ queryKey: fichaQueryKey(loteId) });
    },
  });
}
