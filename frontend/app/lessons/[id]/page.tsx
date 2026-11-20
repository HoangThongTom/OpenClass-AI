"use client";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ArrowRight, BookOpenText, CheckCircle2, ChevronLeft, ChevronRight, CircleAlert, Clock3, FileText, FlaskConical, GraduationCap, HelpCircle, Layers, Lightbulb, LoaderCircle, RotateCcw, Sparkles, Trash2, WandSparkles } from "lucide-react";
import { Shell } from "@/components/Shell";
import { HarrisLab } from "@/components/HarrisLab";
import { OutlineReview } from "@/components/OutlineReview";
import { SlideEditor } from "@/components/SlideEditor";
import { CreateLessonModal } from "@/components/CreateLessonModal";
import { api } from "@/lib/api";
import type { Lesson } from "@/lib/types";

type Tab = "slides" | "quiz" | "flashcards" | "lab";

export default function LessonPage() {
  const params = useParams<{id: string}>();
  const router = useRouter();
  const id = params.id;
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<Tab>("slides");
  const [slideIndex, setSlideIndex] = useState(0);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [cardIndex, setCardIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [working, setWorking] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [retryOpen, setRetryOpen] = useState(false);
  const [models, setModels] = useState<string[]>([]);
  useEffect(() => {
    if (!retryOpen) return;
    void api.models().then(result => setModels(result.models)).catch(() => setModels([]));
  }, [retryOpen]);
  const fetchLesson = useCallback(async () => {
    try { setLesson(await api.lesson(id)); setError(""); }
    catch (e) { setError(e instanceof Error ? e.message : "Không thể tải bài học."); }
  }, [id]);
  useEffect(() => { void fetchLesson(); const interval = setInterval(() => void fetchLesson(), 3000); return () => clearInterval(interval); }, [fetchLesson]);
  useEffect(() => { if (lesson?.status !== "generating") return; const timer = setInterval(() => setElapsed(x => x + 1), 1000); return () => clearInterval(timer); }, [lesson?.status]);

  const content = lesson?.content;
  const slides = content?.slides || [];
  const quiz = content?.quiz || [];
  const flashcards = content?.flashcards || [];
  const showLab = useMemo(() => `${lesson?.title || ""} ${lesson?.topic || ""}`.toLowerCase().includes("harris"), [lesson]);
  const completed = quiz.filter((_, i) => answers[i] !== undefined).length;
  const correct = quiz.filter((q, i) => answers[i] === q.correct_index).length;

  function regenerated(updated: Lesson) {
    setLesson(updated); setError(""); setElapsed(0); setTab("slides");
    setSlideIndex(0); setQuestionIndex(0); setAnswers({}); setCardIndex(0); setFlipped(false);
  }
  async function resume() {
    if (!lesson) return;
    setWorking(true);
    try { regenerated(await api.resume(lesson.id)); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Không tiếp tục được bài học."); }
    finally { setWorking(false); }
  }
  const stage = lesson?.workspace?.stage;
  const stageLabel = stage === "outline" ? "Đang tạo dàn ý" : stage === "exercises" ? "Đang soạn quiz và flashcards" : stage?.startsWith("slide:") ? `Đang tạo slide ${stage.split(":")[1]}/${lesson?.slide_count}` : "AI đang biên soạn nội dung";
  async function remove() {
    if (!lesson || !confirm("Bạn chắc chắn muốn xóa bài học này?")) return;
    setWorking(true);
    try { await api.remove(lesson.id); router.push("/"); }
    catch (e) { setError(e instanceof Error ? e.message : "Không thể xóa bài học."); setWorking(false); }
  }

  return <Shell><div className="page-container lesson-page">
    <header className="topbar"><div className="breadcrumbs"><Link href="/">Workspace</Link><ChevronRight size={14}/><Link href="/#library">Thư viện</Link><ChevronRight size={14}/><strong>Bài học</strong></div><span className="system-pill connected"><span className="online-dot"/> LOCAL CLASSROOM</span></header>
    <Link href="/" className="back-link"><ArrowLeft size={16}/> Quay về tổng quan</Link>
    {error && <div className="alert-box"><CircleAlert size={18}/>{error}</div>}
    {!lesson ? <div className="loader-panel"><LoaderCircle className="spin" size={30}/> Đang tải bài học...</div> : <>
      <div className="lesson-header"><div><div className="section-overline"><span className="tiny-gradient-dot"/> INTERACTIVE CLASSROOM</div><h1>{lesson.title}<span className="title-period">.</span></h1><div className="lesson-submeta"><span><Layers size={15}/> {lesson.status === "ready" ? (content?.slides.length ?? lesson.slide_count) : lesson.slide_count} slides</span><span><GraduationCap size={15}/> {lesson.model}</span>{lesson.source_name && <span><FileText size={15}/> {lesson.source_name}</span>}</div></div><span className={`status-tag status-header ${lesson.status}`}>{lesson.status === "ready" ? "● Sẵn sàng" : lesson.status === "generating" ? "◌ Đang soạn bài" : lesson.status === "failed" ? "● Tạo thất bại" : "Bản nháp"}</span></div>
      {lesson.workspace?.source_warning && <div className="alert-box">{lesson.workspace.source_warning}</div>}
      {lesson.workspace && <div className="generation-summary"><span>{lesson.workspace.mode === "balanced" ? "Cân bằng" : "Nhanh"} · Đã lưu {lesson.workspace.completed_slides}/{lesson.slide_count} slide</span><span>Tổng thời gian xử lý: {lesson.workspace.elapsed_seconds.toFixed(1)} giây</span></div>}
      {lesson.workspace?.outline && !lesson.workspace.approved && lesson.status !== "generating" && <OutlineReview lesson={lesson} onUpdated={regenerated}/>}
      {lesson.status === "generating" && <div className="generation-screen"><div className="generation-orb"><div className="generation-orb-inner"><WandSparkles size={34}/></div></div><div className="eyebrow">AI IS WORKING</div><h2>{stageLabel}</h2><p>Ollama đang đọc tài liệu, xây dựng slide và soạn câu hỏi. Với model local, quá trình này có thể mất vài phút.</p><div className="generation-steps"><span><LoaderCircle className="spin" size={17}/> {stageLabel}</span><span><Clock3 size={17}/> Đã chạy {Math.floor(elapsed / 60)}:{String(elapsed % 60).padStart(2,"0")}</span></div><div className="generation-rail"><i/></div><small>Trang này tự cập nhật mỗi 3 giây. Không cần mở thêm nhiều lần tạo bài.</small></div>}
      {lesson.status === "failed" && <div className="failure-screen"><span className="failure-icon"><CircleAlert size={34}/></span><h2>Chưa thể tạo bài học</h2><p>{lesson.error || "Model local chưa phản hồi. Kiểm tra Ollama trước khi thử lại."}</p><div className="failure-actions">{lesson.workspace && <button className="btn btn-primary" disabled={working} onClick={() => void resume()}>Tiếp tục phần đang dở</button>}<button className="btn btn-primary" onClick={() => setRetryOpen(true)} disabled={working}>{working ? <LoaderCircle size={18} className="spin"/> : <RotateCcw size={18}/>} Tạo dàn ý mới</button><button className="btn btn-ghost" onClick={() => void remove()} disabled={working}><Trash2 size={16}/> Xóa bài học</button></div><div className="failure-tip"><b>Gợi ý:</b> chạy <code>ollama list</code> rồi thử tạo bài ngắn hơn (2–3 slide). Nếu có lỗi timeout, kiểm tra log FastAPI.</div></div>}
      {lesson.status === "ready" && content && <>
        <div className="classroom-tabs"><button onClick={() => setTab("slides")} className={tab === "slides" ? "selected" : ""}><BookOpenText size={17}/> Bài giảng <span>{slides.length}</span></button><button onClick={() => setTab("quiz")} className={tab === "quiz" ? "selected" : ""}><HelpCircle size={17}/> Trắc nghiệm <span>{quiz.length}</span></button><button onClick={() => setTab("flashcards")} className={tab === "flashcards" ? "selected" : ""}><Layers size={17}/> Flashcards <span>{flashcards.length}</span></button>{showLab && <button onClick={() => setTab("lab")} className={tab === "lab" ? "selected" : ""}><FlaskConical size={17}/> Harris Lab <span className="experimental-badge">LIVE</span></button>}</div>
        {tab === "slides" && <div className="slides-workspace"><aside className="slides-nav"><div className="slides-nav-header"><span className="eyebrow">COURSE OUTLINE</span><h3>Nội dung bài học</h3></div>{slides.map((s, i) => <button key={i} onClick={() => setSlideIndex(i)} className={`slide-nav-item ${slideIndex === i ? "selected" : ""}`}><span>{String(i + 1).padStart(2,"0")}</span><b>{s.title}</b>{slideIndex === i && <span className="current-dot"/>}</button>)}<div className="outline-bottom"><Sparkles size={17}/><p>{content.summary}</p></div></aside><div className="slide-view"><div className="slide-top"><span><span className="slide-top-dot"/> SLIDE {slideIndex + 1} / {slides.length}</span><span>OPENCLASS AI ORIGINAL</span></div><div className="slide-canvas"><div className="slide-accent-bar"/><div className="slide-counter">{String(slideIndex + 1).padStart(2,"0")}</div><div className="slide-kicker">KEY CONCEPT / {String(slideIndex + 1).padStart(2,"0")}</div><h2>{slides[slideIndex]?.title}</h2><div className="slide-callout"><Lightbulb size={23}/><p>{slides[slideIndex]?.key_point}</p></div><div className="bullet-list">{slides[slideIndex]?.bullets.map((b, i) => <div key={i}><span className="bullet-number">{String(i + 1).padStart(2,"0")}</span><p>{b}</p></div>)}</div><div className="slide-watermark"><GraduationCap size={66}/></div></div><div className="speaker-notes"><Lightbulb size={17}/><p><b>Ghi chú giảng viên: </b>{slides[slideIndex]?.speaker_notes || "Hãy thử tự giải thích nội dung slide bằng ví dụ của riêng bạn."}</p></div><div className="slides-footer"><span>Tiến độ <b>{Math.round(((slideIndex + 1) / slides.length) * 100)}%</b></span><div className="slides-progress"><span style={{ width: `${((slideIndex + 1) / slides.length) * 100}%` }}/></div><div className="slides-controls"><button onClick={() => setSlideIndex(i => Math.max(0, i - 1))} disabled={slideIndex === 0}><ChevronLeft size={18}/> Trước</button><button className="next-slide" onClick={() => slideIndex === slides.length - 1 ? setTab("quiz") : setSlideIndex(i => Math.min(slides.length - 1, i + 1))}>{slideIndex === slides.length - 1 ? "Làm quiz" : "Tiếp theo"} <ArrowRight size={17}/></button></div></div></div></div>}
        {tab === "slides" && <SlideEditor lesson={lesson} index={slideIndex} onUpdated={updated => { setLesson(updated); setError(""); setElapsed(0); }}/>}
        {tab === "quiz" && <div className="learning-section quiz-section"><div className="learning-intro"><span className="eyebrow">KNOWLEDGE CHECK</span><h2>Kiểm tra kiến thức<span className="title-period">.</span></h2><p>Chọn đáp án cho từng câu để kiểm tra mức độ hiểu bài. Kết quả được chấm ngay trên trình duyệt.</p></div>{quiz.length ? <div className="quiz-card"><div className="quiz-meta"><span>CÂU HỎI {questionIndex + 1} / {quiz.length}</span><span>{completed}/{quiz.length} hoàn thành</span></div><div className="quiz-dots">{quiz.map((_,i) => <button aria-label={`Câu ${i+1}`} key={i} onClick={() => setQuestionIndex(i)} className={`${i === questionIndex ? "current" : ""} ${answers[i] !== undefined ? "answered" : ""}`} />)}</div><h3>{quiz[questionIndex].question}</h3><div className="quiz-options">{quiz[questionIndex].options.map((option, index) => { const selected = answers[questionIndex] === index; const answered = answers[questionIndex] !== undefined; const isCorrect = index === quiz[questionIndex].correct_index; return <button key={index} disabled={answered} onClick={() => setAnswers(prev => ({...prev,[questionIndex]:index}))} className={`quiz-option ${selected ? "picked" : ""} ${answered && isCorrect ? "right" : ""} ${selected && !isCorrect ? "wrong" : ""}`}><span className="option-letter">{String.fromCharCode(65+index)}</span><span>{option}</span>{answered && isCorrect && <CheckCircle2 size={18}/>}</button>; })}</div>{answers[questionIndex] !== undefined && <div className="quiz-explanation"><strong>{answers[questionIndex] === quiz[questionIndex].correct_index ? "Chính xác!" : "Đáp án đúng đã được đánh dấu."}</strong><p>{quiz[questionIndex].explanation}</p></div>}<div className="quiz-footer"><div><b>{correct}</b> câu đúng / {completed} đã trả lời</div><div className="quiz-controls"><button onClick={() => setQuestionIndex(i => Math.max(0,i-1))} disabled={questionIndex === 0}><ChevronLeft size={18}/></button><button onClick={() => setQuestionIndex(i => Math.min(quiz.length-1,i+1))} disabled={questionIndex === quiz.length-1}><ChevronRight size={18}/></button></div></div>{completed === quiz.length && <div className="quiz-complete"><GraduationCap size={20}/> Bạn đạt <b>{Math.round(100*correct/quiz.length)}%</b> · <button onClick={() => {setAnswers({});setQuestionIndex(0);}}>Làm lại bài quiz</button></div>}</div> : <div className="loader-panel">Bài giảng này chưa có câu hỏi trắc nghiệm.</div>}</div>}
        {tab === "flashcards" && <div className="learning-section flashcard-section"><div className="learning-intro"><span className="eyebrow">ACTIVE RECALL</span><h2>Thẻ ghi nhớ<span className="title-period">.</span></h2><p>Lật thẻ để xem giải thích. Nhớ trước khi lật là cách luyện tập chủ động hiệu quả.</p></div>{flashcards.length ? <><button className={`flashcard-main ${flipped ? "is-flipped" : ""}`} onClick={() => setFlipped(x => !x)}><div className="flashcard-label">{flipped ? "GIẢI THÍCH" : "KHÁI NIỆM"} <span>{cardIndex + 1} / {flashcards.length}</span></div><div className="flashcard-word">{flipped ? flashcards[cardIndex].back : flashcards[cardIndex].front}</div><span className="flashcard-flip"><RotateCcw size={16}/> Nhấn để lật thẻ</span></button><div className="flashcard-nav"><button onClick={() => {setCardIndex(i => Math.max(i-1,0));setFlipped(false);}} disabled={cardIndex === 0}><ChevronLeft size={18}/> Thẻ trước</button><span>{flashcards.map((_,i) => <span key={i} className={`flashcard-dot ${i===cardIndex ? "active" : ""}`}/>)}</span><button onClick={() => {setCardIndex(i => Math.min(i+1,flashcards.length-1));setFlipped(false);}} disabled={cardIndex === flashcards.length-1}>Thẻ tiếp <ChevronRight size={18}/></button></div></> : <div className="loader-panel">Bài học này chưa có flashcard.</div>}</div>}
        {tab === "lab" && showLab && <HarrisLab/>}
        <div className="lesson-bottom-actions"><button className="btn btn-ghost" disabled={working} onClick={() => setRetryOpen(true)}><RotateCcw size={16}/> Tạo lại</button><span><Sparkles size={16}/> Generated by {lesson.model}</span><button className="delete-lesson" disabled={working} onClick={() => void remove()}><Trash2 size={16}/> Xóa bài học</button></div>
      </>}
    </>}
  </div>{lesson && <CreateLessonModal open={retryOpen} onClose={() => setRetryOpen(false)} availableModels={models} retryLesson={lesson} onRegenerated={regenerated}/>}</Shell>;
}
