/** Espelha backend/app/services/numeros.py — o parser de verdade roda no servidor; isto
 * serve só para validação otimista no input antes de disparar o autosave. */
export function parseNumberBR(texto: string): number | null {
  const limpo = texto.trim();
  if (limpo === "") return null;

  let normalizado = limpo;
  if (limpo.includes(",")) {
    normalizado = limpo.replaceAll(".", "").replace(",", ".");
  } else {
    const partes = limpo.split(".");
    const ultimaParteEhMilhar = partes.length > 1 && partes.at(-1)?.length === 3 && partes.every((p) => /^\d+$/.test(p));
    if (ultimaParteEhMilhar) {
      normalizado = limpo.replaceAll(".", "");
    }
  }

  const numero = Number(normalizado);
  return Number.isNaN(numero) ? null : numero;
}

export function isValidNumberInput(texto: string): boolean {
  return texto.trim() === "" || parseNumberBR(texto) !== null;
}
