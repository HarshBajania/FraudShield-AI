export async function api<T>(
  path: string,
  options?: RequestInit,
  signal?: AbortSignal,
): Promise<T> {
  const key = sessionStorage.getItem("fraud-api-key");
  const response = await fetch(`/api${path}`, {
    ...options,
    signal,
    headers: {
      "Content-Type": "application/json",
      ...(key ? { "X-API-Key": key } : {}),
      ...options?.headers,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail =
      typeof body?.detail === "string"
        ? body.detail
        : body?.detail
          ? JSON.stringify(body.detail)
          : response.statusText;
    throw new Error(`${response.status}: ${detail}`);
  }
  return response.json() as Promise<T>;
}
export const number = (value: number) =>
  new Intl.NumberFormat("en", { maximumFractionDigits: 0 }).format(value);
export const amount = (value: number) =>
  new Intl.NumberFormat("en", {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  }).format(value);
export const percent = (value: number) => `${(value * 100).toFixed(1)}%`;
