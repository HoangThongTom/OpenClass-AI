import type { GenerationMode, Health, Lesson, Models, Outline, Slide } from "./types";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, { cache: "no-store", ...options });
  } catch {
    throw new Error("Không kết nối được API. Kiểm tra FastAPI tại http://localhost:8000/docs.");
  }
  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try {
      const error = await response.json();
      message = typeof error.detail === "string" ? error.detail
        : Array.isArray(error.detail) ? `Dữ liệu chưa hợp lệ: ${error.detail.map((item: { msg: string }) => item.msg).join("; ")}` : message;
    } catch { /* preserve HTTP code */ }
    throw new Error(message);
  }
  return (response.status === 204 ? undefined : response.json()) as Promise<T>;
}

export const api = {
  health: () => request<Health>("/health"),
  models: () => request<Models>("/models"),
  modelInfo: (model: string) => request<{ model: string; capabilities: string[]; thinking: unknown }>(`/model-info?model=${encodeURIComponent(model)}`),
  lessons: () => request<Lesson[]>("/lessons"),
  lesson: (id: string) => request<Lesson>(`/lessons/${encodeURIComponent(id)}`),
  create: (form: FormData) => request<Lesson>("/lessons", { method: "POST", body: form }),
  demo: () => request<Lesson>("/demo", { method: "POST" }),
  regenerate: (id: string, options: { model: string; slide_count: number; mode?: GenerationMode }) => request<Lesson>(`/lessons/${encodeURIComponent(id)}/generate`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(options),
  }),
  saveOutline: (id: string, outline: Outline) => request<Lesson>(`/lessons/${encodeURIComponent(id)}/outline`, {
    method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(outline),
  }),
  approve: (id: string, outline: Outline) => request<Lesson>(`/lessons/${encodeURIComponent(id)}/approve`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(outline),
  }),
  resume: (id: string) => request<Lesson>(`/lessons/${encodeURIComponent(id)}/resume`, { method: "POST" }),
  editSlide: (id: string, index: number, slide: Omit<Slide, "sources">) => request<Lesson>(`/lessons/${encodeURIComponent(id)}/slides/${index}`, {
    method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(slide),
  }),
  regenerateSlide: (id: string, index: number) => request<Lesson>(`/lessons/${encodeURIComponent(id)}/slides/${index}/generate`, { method: "POST" }),
  remove: (id: string) => request<void>(`/lessons/${encodeURIComponent(id)}`, { method: "DELETE" }),
};
