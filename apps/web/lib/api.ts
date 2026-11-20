const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
export function token() { return typeof window === "undefined" ? null : window.localStorage.getItem("buildatlas_token"); }
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API}${path}`, { ...options, headers: { "Content-Type": "application/json", ...(token() ? { Authorization: `Bearer ${token()}` } : {}), ...options.headers } });
  if (response.status === 401 && typeof window !== "undefined") { window.localStorage.removeItem("buildatlas_token"); window.location.href = "/login"; }
  if (!response.ok) { const data = await response.json().catch(() => ({})); throw new Error(data.detail?.error?.message ?? data.detail ?? "Request failed"); }
  return response.status === 204 ? undefined as T : response.json();
}
export type Project = {id:string;name:string;description:string;constraints:Record<string,unknown>;status:string;created_at:string};
