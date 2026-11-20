"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronDown, FileText, FileUp, LoaderCircle, SlidersHorizontal, Sparkles, X } from "lucide-react";
import { api } from "@/lib/api";
import type { GenerationMode, Lesson } from "@/lib/types";

const MAX_FILES = 5;
const MAX_FILE_MB = 15;
const MAX_TOTAL_MB = 30;
const MB = 1024 * 1024;
const ALLOWED_EXTENSIONS = /\.(pdf|md|markdown|txt)$/i;

export function CreateLessonModal({ open, onClose, availableModels, retryLesson, onRegenerated }: {
  open: boolean; onClose: () => void; availableModels: string[];
  retryLesson?: Lesson; onRegenerated?: (lesson: Lesson) => void;
}) {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [topic, setTopic] = useState("");
  const [model, setModel] = useState("");
  const [slides, setSlides] = useState(3);
  const [files, setFiles] = useState<File[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [mode, setMode] = useState<GenerationMode>("fast");
  const [modelStatus, setModelStatus] = useState("");
  const [modelValid, setModelValid] = useState(false);

  useEffect(() => {
    if (!open || !model) return;
    let current = true;
    setModelValid(false); setModelStatus("Đang kiểm tra khả năng model...");
    void api.modelInfo(model).then(() => {
      if (current) { setModelValid(true); setModelStatus("Model local hỗ trợ tạo bài. Context 4K phù hợp cấu hình máy hiện tại."); }
    }).catch(cause => { if (current) setModelStatus(cause instanceof Error ? cause.message : "Không kiểm tra được model."); });
    return () => { current = false; };
  }, [model, open]);

  useEffect(() => {
    if (open) {
      setError("");
      setBusy(false);
      setSlides(retryLesson?.slide_count ?? 3);
      setMode(retryLesson?.workspace?.mode ?? "fast");
    }
  }, [open, retryLesson?.id, retryLesson?.slide_count]);

  useEffect(() => {
    if ((!model || !availableModels.includes(model)) && availableModels.length) {
      setModel(availableModels.includes("qwen2.5:3b") ? "qwen2.5:3b" : availableModels[0]);
    }
  }, [availableModels, model]);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => { if (event.key === "Escape" && !busy) onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, busy, onClose]);

  const addFiles = (selected: FileList | null) => {
    if (!selected || busy) return;
    const incoming = Array.from(selected);
    const fresh = incoming.filter(candidate =>
      !files.some(existing => existing.name === candidate.name && existing.size === candidate.size && existing.lastModified === candidate.lastModified)
    );
    if (fresh.length === 0) {
      setError("Những tài liệu này đã có trong danh sách.");
      return;
    }
    if (files.length + fresh.length > MAX_FILES) {
      setError(`Mỗi bài học được chọn tối đa ${MAX_FILES} tài liệu.`);
      return;
    }
    const invalid = fresh.find(file => !ALLOWED_EXTENSIONS.test(file.name));
    if (invalid) {
      setError(`${invalid.name}: chỉ hỗ trợ PDF, Markdown (.md) hoặc TXT.`);
      return;
    }
    const tooLarge = fresh.find(file => file.size > MAX_FILE_MB * MB);
    if (tooLarge) {
      setError(`${tooLarge.name}: vượt giới hạn ${MAX_FILE_MB} MB/tệp.`);
      return;
    }
    if ([...files, ...fresh].reduce((sum, item) => sum + item.size, 0) > MAX_TOTAL_MB * MB) {
      setError(`Tổng dung lượng tài liệu không được vượt ${MAX_TOTAL_MB} MB.`);
      return;
    }
    setFiles([...files, ...fresh]);
    setError("");
  };

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!availableModels.includes(model) || !modelValid) {
      setError("Hãy chọn một model đã cài trong Ollama.");
      return;
    }
    setBusy(true);
    setError("");
    const data = new FormData();
    data.set("title", title);
    data.set("topic", topic);
    data.set("model", model || "qwen2.5:3b");
    data.set("slide_count", String(slides));
    data.set("mode", mode);
    files.forEach(file => data.append("files", file, file.name));
    try {
      if (retryLesson) {
        const lesson = await api.regenerate(retryLesson.id, { model, slide_count: slides, mode });
        onRegenerated?.(lesson);
        setBusy(false);
        onClose();
      } else {
        const lesson = await api.create(data);
        router.push(`/lessons/${lesson.id}`);
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể tạo bài học.");
      setBusy(false);
    }
  };

  if (!open) return null;

  return (
    <div className="modal-backdrop" onMouseDown={event => { if (event.target === event.currentTarget && !busy) onClose(); }} role="presentation">
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <div className="modal-heading">
          <div className="modal-icon"><Sparkles size={22}/></div>
          <div><span className="eyebrow">INTERACTIVE CLASS</span><h2 id="modal-title">{retryLesson ? "Tạo lại bài học" : "Tạo bài học mới"}</h2></div>
          <button type="button" className="icon-button close-modal" disabled={busy} onClick={onClose} aria-label="Đóng"><X size={20}/></button>
        </div>
        <p className="modal-description">{retryLesson ? `Chọn model và số slide mới cho “${retryLesson.title}”. Tài liệu đã lưu sẽ được sử dụng lại.` : "Chọn chủ đề, đính kèm tối đa 5 tài liệu. AI local sẽ tạo slide, quiz và flashcard."}</p>
        <form onSubmit={submit} className="create-form">
          {!retryLesson && <>
          <div className="field-group">
            <label htmlFor="lesson-title">Tên lớp học <span>*</span></label>
            <input id="lesson-title" value={title} onChange={event => setTitle(event.target.value)} required minLength={3} maxLength={180} placeholder="Ví dụ: Harris Corner Detection từ A–Z"/>
          </div>
          <div className="field-group">
            <label htmlFor="lesson-topic">Bạn muốn học gì? <span>*</span></label>
            <textarea id="lesson-topic" value={topic} onChange={event => setTopic(event.target.value)} required minLength={3} maxLength={1500} rows={3} placeholder="Giải thích nguyên lý, công thức, ví dụ thực tế và bài tập ôn tập..."/>
          </div>
          <div className="field-group">
            <label>Đính kèm tài liệu <small>(không bắt buộc)</small></label>
            <label className={`upload-zone ${files.length ? "uploaded" : ""}`} onDragOver={event => event.preventDefault()} onDrop={event => { event.preventDefault(); addFiles(event.dataTransfer.files); }}>
              <input
                aria-label="Chọn nhiều tài liệu"
                type="file"
                multiple
                disabled={busy}
                accept=".pdf,.md,.markdown,.txt"
                onChange={event => { addFiles(event.target.files); event.target.value = ""; }}
              />
              <span className="upload-icon"><FileUp size={23}/></span>
              <span>
                <b>{files.length ? `Đã chọn ${files.length}/${MAX_FILES} tài liệu · Thêm tài liệu` : "Chọn nhiều PDF, Markdown hoặc TXT"}</b>
                <small>Kéo thả hoặc bấm chọn · {MAX_FILE_MB} MB/tệp · tổng {MAX_TOTAL_MB} MB</small>
              </span>
            </label>
            {files.length > 0 && (
              <div className="upload-file-list" aria-label="Các tài liệu đã chọn">
                {files.map((file, index) => (
                  <div className="upload-file-item" key={`${file.name}-${file.size}-${file.lastModified}`}>
                    <FileText size={15}/>
                    <span title={file.name}>{file.name}</span>
                    <small>{(file.size / MB).toFixed(2)} MB</small>
                    <button type="button" disabled={busy} onClick={() => setFiles(current => current.filter((_, i) => i !== index))} aria-label={`Xóa ${file.name}`} title={`Xóa ${file.name}`}><X size={15}/></button>
                  </div>
                ))}
              </div>
            )}
          </div>
          </>}
          <div className="field-group">
            <label htmlFor="generation-mode">Chế độ soạn bài</label>
            <select id="generation-mode" disabled={busy} value={mode} onChange={event => {
              const next = event.target.value as GenerationMode; setMode(next);
              const suggested = next === "fast" ? "qwen2.5:3b" : "qwen3:4b";
              if (availableModels.includes(suggested)) setModel(suggested);
            }}>
              <option value="fast">Nhanh · nội dung ngắn gọn</option>
              <option value="balanced">Cân bằng · giải thích và ví dụ</option>
            </select>
            <small>{mode === "fast" ? "Đề xuất qwen2.5:3b." : "Đề xuất qwen3:4b nếu đã cài; bạn vẫn có thể chọn model khác."} AI sẽ tạo dàn ý để bạn duyệt trước.</small>
          </div>
          <div className="form-grid">
            <div className="field-group">
              <label htmlFor="lesson-model">Model Ollama</label>
              <div className="select-wrapper">
                <select id="lesson-model" value={model} disabled={busy || !availableModels.length} onChange={event => setModel(event.target.value)}>
                  {!availableModels.length && <option value="">Chưa có model khả dụng</option>}
                  {availableModels.map(item => <option key={item} value={item}>{item}</option>)}
                </select><ChevronDown size={16}/>
              </div>
            </div>
            <div className="field-group">
              <label htmlFor="lesson-slides"><SlidersHorizontal size={14}/> Số slide <span className="slide-count">{slides}</span></label>
              <input id="lesson-slides" type="range" min={2} max={6} disabled={busy} value={slides} onChange={event => setSlides(Number(event.target.value))}/>
              <div className="range-labels"><small>2 · Nhanh</small><small>6 · Chi tiết</small></div>
            </div>
          </div>
          {modelStatus && <p className={modelValid ? "model-check" : "form-error"} role="status">{modelStatus}</p>}
          {!availableModels.length && <div className="form-error" role="alert">Không có model khả dụng. Kiểm tra Ollama, cài qwen2.5:3b rồi tải lại trang.</div>}
          {error && <div className="form-error" role="alert">{error}</div>}
          <div className="modal-actions">
            <button type="button" className="btn btn-ghost" onClick={onClose} disabled={busy}>Hủy</button>
            <button className="btn btn-primary" type="submit" disabled={busy || !modelValid || !availableModels.includes(model)}>
              {busy ? <LoaderCircle size={18} className="spin"/> : <Sparkles size={18}/>}
              {busy ? "Đang gửi yêu cầu..." : retryLesson ? "Tạo dàn ý mới" : "Tạo dàn ý để duyệt"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
