"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Lesson, Slide } from "@/lib/types";

export function SlideEditor({ lesson, index, onUpdated }: { lesson: Lesson; index: number; onUpdated: (lesson: Lesson) => void }) {
  const slide = lesson.content?.slides[index];
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<Slide | null>(slide ?? null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => { setEditing(false); setError(""); }, [index, lesson.id]);
  if (!slide) return null;
  async function submit(regenerate: boolean) {
    if (!draft) return;
    setBusy(true); setError("");
    try {
      const { sources: _, ...fields } = draft;
      const updated = regenerate ? await api.regenerateSlide(lesson.id, index) : await api.editSlide(lesson.id, index, fields);
      onUpdated(updated); setEditing(false);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Không cập nhật được slide."); }
    finally { setBusy(false); }
  }
  return <section className="slide-editor">
    <div className="editor-actions">
      <button className="btn btn-ghost" disabled={busy} onClick={() => { setDraft({ ...slide, bullets: [...slide.bullets] }); setEditing(value => !value); }}>{editing ? "Đóng chỉnh sửa" : "Chỉnh slide này"}</button>
      <button className="btn btn-ghost" disabled={busy} onClick={() => void submit(true)}>{busy ? "Đang gửi..." : "AI tạo lại slide này"}</button>
    </div>
    {editing && draft && <form onSubmit={event => { event.preventDefault(); void submit(false); }}>
      <fieldset disabled={busy}>
        <div className="field-group"><label htmlFor="edit-slide-title">Tiêu đề</label><input id="edit-slide-title" required value={draft.title} onChange={event => setDraft({ ...draft, title: event.target.value })}/></div>
        <div className="field-group"><label htmlFor="edit-slide-point">Ý chính</label><textarea id="edit-slide-point" required value={draft.key_point} onChange={event => setDraft({ ...draft, key_point: event.target.value })}/></div>
        <div className="field-group"><label htmlFor="edit-slide-bullets">Gạch đầu dòng · mỗi dòng một ý, tối đa 5 ý</label><textarea id="edit-slide-bullets" required rows={4} value={draft.bullets.join("\n")} onChange={event => setDraft({ ...draft, bullets: event.target.value.split("\n") })}/></div>
        <div className="field-group"><label htmlFor="edit-slide-notes">Ghi chú giảng viên</label><textarea id="edit-slide-notes" value={draft.speaker_notes} onChange={event => setDraft({ ...draft, speaker_notes: event.target.value })}/></div>
        <button className="btn btn-primary" disabled={busy}>Lưu slide</button>
      </fieldset>
    </form>}
    {error && <div className="form-error" role="alert">{error}</div>}
    <small>Quiz và flashcards được giữ nguyên khi sửa riêng slide. Hãy kiểm tra lại nếu thay đổi kiến thức.</small>
    {!!slide.sources?.length && <div className="slide-sources"><h4>Đoạn tài liệu được dùng để soạn slide</h4>
      <small>Dẫn nguồn giúp đối chiếu; bạn vẫn cần kiểm tra cách AI diễn giải.</small>
      {slide.sources.map((source, i) => <details key={`${source.document_id}-${source.page}-${i}`}>
        <summary>{source.filename}{source.page ? ` · trang ${source.page}` : " · không có số trang gốc"}</summary>
        <blockquote>{source.excerpt}</blockquote>
      </details>)}
    </div>}
  </section>;
}
