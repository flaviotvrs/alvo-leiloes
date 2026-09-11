import type { Origem } from "../api/types";

export type OrigemOuVazio = Origem | "vazio";

interface EspecificacaoProcedencia {
  rotulo: string;
  quadradoBg: string;
  quadradoBorda: string;
  quadradoTracejado: boolean;
  chipBg: string;
  chipTexto: string;
}

/** README "Marcadores de procedência do dado" — os quatro estados (mais "vazio", que não
 * é um valor de `origem` real, é a ausência de linha em `campos`). */
export const ESPECIFICACAO_PROCEDENCIA: Record<OrigemOuVazio, EspecificacaoProcedencia> = {
  base: {
    rotulo: "Caixa",
    quadradoBg: "#C9C4B6",
    quadradoBorda: "#B8B2A3",
    quadradoTracejado: false,
    chipBg: "#E4E0D6",
    chipTexto: "#5C584C",
  },
  manual: {
    rotulo: "Manual",
    quadradoBg: "#1F6F4A",
    quadradoBorda: "#1F6F4A",
    quadradoTracejado: false,
    chipBg: "#E6EEE9",
    chipTexto: "#1F6F4A",
  },
  automacao: {
    rotulo: "Automático",
    quadradoBg: "#D9B84F",
    quadradoBorda: "#B79A2F",
    quadradoTracejado: false,
    chipBg: "#F7EFDC",
    chipTexto: "#8A6B14",
  },
  coleta_guiada: {
    // ainda não desenhado no README como estado visual próprio — hoje some junto de "manual"
    rotulo: "Manual",
    quadradoBg: "#1F6F4A",
    quadradoBorda: "#1F6F4A",
    quadradoTracejado: false,
    chipBg: "#E6EEE9",
    chipTexto: "#1F6F4A",
  },
  vazio: {
    rotulo: "A preencher",
    quadradoBg: "transparent",
    quadradoBorda: "#B8B2A3",
    quadradoTracejado: true,
    chipBg: "#F2F0EB",
    chipTexto: "#8A8577",
  },
};
