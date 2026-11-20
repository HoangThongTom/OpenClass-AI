"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Lesson, Outline } from "@/lib/types";

export function OutlineReview({ lesson, onUpdated }: { lesson: Lesson; onUpdated: (lesson: Lesson) => void }) {
  const saved = JSON.stringify(lesson.workspace?.outline ?? null);
  const [outline, setOutline] = useState<Outline | null>(lesson.workspace?.outline ?? null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  useEffect(() => { setOutline(JSON.parse(saved) ?? null); }, [saved]);
  if (!outline) return null;
  async function submit(approve: boolean) {
    if (!outline) return;
    setBusy(true); setError(""); setNotice("");
    try {
      const updated = approve ? await api.approve(lesson.id, outline) : await api.saveOutline(lesson.id, outline);
      onUpdated(updated);
      if (!approve) setNotice("Đã lưu dàn ý.");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Không lưu được dàn ý."); }
    finally { setBusy(false); }
  }
  function change(index: number, field: "title" | "focus", value: string) {
    setOutline(current => current ? { ...current, slides: current.slides.map((slide, i) => i === index ? { ...slide, [field]: value } : slide) } : null);
  }
  return <section className="review-panel">
    <span className="eyebrow">DÀN Ý ĐANG CHỜ DUYỆT</span>
    <h2>Chỉnh dàn ý trước khi soạn bài</h2>
    <p>AI sẽ tạo từng slide theo nội dung bạn duyệt, sau đó soạn quiz và flashcards.</p>
    <form onSubmit={event => { event.preventDefault(); void submit(true); }}>
      <fieldset disabled={busy}>
        <div className="field-group"><label htmlFor="outline-summary">Mục tiêu bài học</label>
          <textarea id="outline-summary" required maxLength={1200} value={outline.summary} onChange={event => setOutline({ ...outline, summary: event.target.value })}/></div>
        {outline.slides.map((slide, index) => <div className="outline-edit-item" key={index}>
          <div className="field-group"><label htmlFor={`outline-title-${index}`}>Slide {index + 1} · Tiêu đề</label>
            <input id={`outline-title-${index}`} required maxLength={180} value={slide.title} onChange={event => change(index, "title", event.target.value)}/></div>
          <div className="field-group"><label htmlFor={`outline-focus-${index}`}>Nội dung cần dạy</label>
            <textarea id={`outline-focus-${index}`} required maxLength={600} value={slide.focus} onChange={event => change(index, "focus", event.target.value)}/></div>
        </div>)}
      </fieldset>
      {error && <div className="form-error" role="alert">{error}</div>}
      {notice && <p role="status">{notice}</p>}
      <div className="editor-actions">
        <button type="button" className="btn btn-ghost" disabled={busy} onClick={() => void submit(false)}>Lưu dàn ý</button>
        <button className="btn btn-primary" disabled={busy}>{busy ? "Đang gửi..." : "Duyệt và tạo bài học"}</button>
      </div>
    </form>
  </section>;
}
