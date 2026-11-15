import type { AskResponse, Coverage, Investigation, RankResponse, Scenario, TestPoints } from "./types";

const BASE: string = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(BASE + path, { headers: { "Content-Type": "application/json" }, ...init });
  } catch {
    throw new Error(`Backend not reachable at ${BASE}. Start it with: cd backend && uvicorn app.main:app --port 8000`);
  }
  if (!res.ok) throw new Error(`${path} returned ${res.status}`);
  return (await res.json()) as T;
}

export const api = {
  coverage: () => call<Coverage>("/coverage"),
  points: () => call<TestPoints>("/points"),
  investigations: () => call<Investigation[]>("/investigations"),
  investigation: (id: string) => call<Investigation>(`/investigations/${encodeURIComponent(id)}`),
  rank: (body: { scenario: Scenario; concern: string; fuel: string; limit: number }) =>
    call<RankResponse>("/rank", { method: "POST", body: JSON.stringify(body) }),
  ask: (question: string) => call<AskResponse>("/ask", { method: "POST", body: JSON.stringify({ question }) }),
};
