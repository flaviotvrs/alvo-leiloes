const BASE_URL = import.meta.env.VITE_API_BASE_URL;
const TOKEN = import.meta.env.VITE_API_BEARER_TOKEN;

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: string,
  ) {
    super(`Erro da API (${status}): ${body}`);
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${TOKEN}`,
      ...options.headers,
    },
  });
  if (!res.ok) {
    throw new ApiError(res.status, await res.text());
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const apiGet = <T>(path: string): Promise<T> => request<T>(path);

export const apiPatch = <T>(path: string, body: unknown): Promise<T> =>
  request<T>(path, { method: "PATCH", body: JSON.stringify(body) });

export const apiPost = <T>(path: string, body?: unknown): Promise<T> =>
  request<T>(path, { method: "POST", body: body !== undefined ? JSON.stringify(body) : undefined });

export async function apiUpload<T>(path: string, arquivo: File): Promise<T> {
  const form = new FormData();
  form.append("arquivo", arquivo);
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${TOKEN}` },
    body: form,
  });
  if (!res.ok) {
    throw new ApiError(res.status, await res.text());
  }
  return (await res.json()) as T;
}

export type QueryValue = string | number | boolean | string[] | undefined | null;

export function buildQuery(params: Record<string, QueryValue>): string {
  const search = new URLSearchParams();
  for (const [chave, valor] of Object.entries(params)) {
    if (valor === undefined || valor === null || valor === "") continue;
    if (Array.isArray(valor)) {
      for (const item of valor) search.append(chave, item);
    } else {
      search.append(chave, String(valor));
    }
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}
