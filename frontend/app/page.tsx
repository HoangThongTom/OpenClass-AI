"use client";
import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, ArrowUpRight, BookMarked, BookOpenText, CheckCircle2, ChevronRight, CircleAlert, Cpu, FileText, FlaskConical, GraduationCap, LayoutDashboard, LoaderCircle, Plus, RefreshCw, Sparkles, WandSparkles, Zap } from "lucide-react";
import { Shell } from "@/components/Shell";
import { CreateLessonModal } from "@/components/CreateLessonModal";
import { api } from "@/lib/api";
import type { Health, Lesson } from "@/lib/types";

function statusLabel(status: Lesson["status"]) {
  return ({ ready: "Sẵn sàng", generating: "Đang tạo", failed: "Lỗi tạo", draft: "Bản nháp" })[status];
}

export default function Home() {
  const router = useRouter();
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [health, setHealth] = useState<Health | null>(null);
  const [apiError, setApiError] = useState("");
  const [modal, setModal] = useState(false);
  const [demoBusy, setDemoBusy] = useState(false);
  const refresh = useCallback(async () => {
    try {
      const [lessonData, healthData] = await Promise.all([api.lessons(), api.health()]);
      setLessons(lessonData); setHealth(healthData); setApiError("");
    } catch (e) { setApiError(e instanceof Error ? e.message : "Không thể kết nối API."); }
  }, []);
  useEffect(() => { void refresh(); const timer = setInterval(() => void refresh(), 7000); return () => clearInterval(timer); }, [refresh]);
  const totalSlides = useMemo(() => lessons.reduce((n, l) => n + (l.content?.slides.length || 0), 0), [lessons]);
  const totalQuiz = useMemo(() => lessons.reduce((n, l) => n + (l.content?.quiz.length || 0), 0), [lessons]);
  const demo = async () => {
    setDemoBusy(true);
    try { const result = await api.demo(); router.push(`/lessons/${result.id}`); }
    catch (e) { setApiError(e instanceof Error ? e.message : "Không thể tạo bài mẫu."); setDemoBusy(false); }
  };
  const models = health?.models ?? [];
  return <Shell>
    <div className="page-container dashboard-page">
      <header className="topbar"><div className="breadcrumbs"><LayoutDashboard size={16} /><span>Workspace</span><ChevronRight size={14}/><strong>Tổng quan</strong></div><div className="top-actions"><span className={`system-pill ${health?.ollama === "online" ? "connected" : "disconnected"}`}><span className="online-dot"/> Ollama {health?.ollama === "online" ? "Online" : "Offline"}</span><span className="header-avatar">OC</span></div></header>
      {apiError && <div className="alert-box"><CircleAlert size={18}/><span>{apiError} — Hãy khởi động backend FastAPI.</span><button onClick={() => void refresh()} title="Thử lại"><RefreshCw size={16}/></button></div>}
      <div className="welcome-row"><div><div className="section-overline"><span className="tiny-gradient-dot"/> AI-POWERED LEARNING WORKSPACE</div><h1>Không gian học tập của bạn<span className="title-period">.</span></h1><p>Tạo bài giảng, khám phá kiến thức và tương tác với AI ngay trên máy của mình.</p></div><button className="btn btn-secondary new-button" onClick={() => setModal(true)}><Plus size={18}/> Tạo lớp mới</button></div>
      <section className="hero-panel"><div className="hero-grid"/><div className="hero-inner"><div className="hero-copy"><div className="hero-kicker"><Sparkles size={14}/> NEXT-GEN AI CLASSROOM <span className="kicker-stroke"/></div><h2>Biến tài liệu thành<br/><span>bài học sống động.</span></h2><p>Thả PDF hoặc Markdown vào. Ollama sẽ biến chúng thành slide, câu hỏi tương tác và thẻ ghi nhớ — hoàn toàn local.</p><div className="hero-actions"><button className="btn btn-primary" onClick={() => setModal(true)}> <WandSparkles size={18}/> Tạo bài học <ArrowRight size={18}/></button><button className="btn btn-hero-outline" onClick={() => void demo()} disabled={demoBusy}>{demoBusy ? <LoaderCircle size={16} className="spin"/> : <FlaskConical size={17}/>} Xem bài mẫu</button></div><div className="hero-foot"><span><CheckCircle2 size={15}/> Không API trả phí</span><span><CheckCircle2 size={15}/> Dữ liệu local</span></div></div><div className="hero-art" aria-hidden="true"><div className="orbit orbit-one"/><div className="orbit orbit-two"/><div className="art-card art-card-back"><span>01 / INPUT</span><FileText size={26}/><b>research-notes.pdf</b><small>DOCUMENT READY</small></div><div className="art-card art-card-front"><div className="art-card-top"><span>02 / AI ENGINE</span><span className="ai-pulse"/></div><div className="art-glow-icon"><GraduationCap size={28}/></div><strong>Interactive class</strong><div className="art-bars"><i/><i/><i/></div><div className="art-progress"> <span/> <b>READY TO LEARN</b></div></div><div className="art-float-icon"><Sparkles size={18}/></div></div></div></section>
      <div className="stat-grid"><div className="stat-card"><div className="stat-head"><span>TỔNG LỚP HỌC</span><span className="stat-icon cyan"><BookOpenText size={18}/></span></div><div className="stat-number">{lessons.length.toString().padStart(2, "0")}</div><div className="stat-detail">Không gian kiến thức đã tạo <ArrowUpRight size={14}/></div></div><div className="stat-card"><div className="stat-head"><span>SLIDE ĐÃ TẠO</span><span className="stat-icon purple"><BookMarked size={18}/></span></div><div className="stat-number">{totalSlides.toString().padStart(2, "0")}</div><div className="stat-detail">Nội dung được AI biên soạn <ArrowUpRight size={14}/></div></div><div className="stat-card"><div className="stat-head"><span>CÂU HỎI ÔN TẬP</span><span className="stat-icon orange"><Zap size={18}/></span></div><div className="stat-number">{totalQuiz.toString().padStart(2, "0")}</div><div className="stat-detail">Học chủ động, nhớ sâu hơn <ArrowUpRight size={14}/></div></div></div>
      <div className="content-grid"><section id="library" className="content-panel library-panel"><div className="panel-heading"><div><span className="eyebrow">YOUR KNOWLEDGE SPACE</span><h3>Thư viện bài học</h3></div><button onClick={() => void refresh()} className="icon-button" aria-label="Làm mới thư viện"><RefreshCw size={18}/></button></div>{lessons.length ? <div className="lesson-list">{lessons.map((lesson, index) => <Link href={`/lessons/${lesson.id}`} className="lesson-row" key={lesson.id}><div className={`lesson-thumb tone-${index % 3}`}><BookOpenText size={23}/><span>{String(index + 1).padStart(2, "0")}</span></div><div className="lesson-row-body"><strong>{lesson.title}</strong><small>{lesson.source_name ? `📄 ${lesson.source_name}` : lesson.topic}</small><div className="lesson-row-meta"><span className={`status-tag ${lesson.status}`}>{lesson.status === "generating" && <span className="tiny-loader"/>}{statusLabel(lesson.status)}</span><span>{lesson.model}</span><span>{lesson.status === "ready" ? (lesson.content?.slides.length ?? lesson.slide_count) : lesson.slide_count} slides</span></div></div><ChevronRight className="lesson-chevron" size={20}/></Link>)}</div> : <div className="empty-state"><div className="empty-illustration"><BookOpenText size={35}/><span className="empty-spark"><Sparkles size={17}/></span></div><h4>Thư viện đang chờ bạn</h4><p>Bài học bạn tạo sẽ xuất hiện tại đây. Khởi động bằng một chủ đề hoặc thử bài mẫu Harris.</p><button className="btn btn-soft" onClick={() => void demo()} disabled={demoBusy}>{demoBusy ? <LoaderCircle className="spin" size={16}/> : <FlaskConical size={16}/>} Dùng bài mẫu Harris</button></div>}</section>
      <section id="studio" className="content-panel studio-panel"><div className="panel-heading"><div><span className="eyebrow">YOUR LOCAL AI</span><h3>AI Studio</h3></div><div className="studio-icon"><Cpu size={19}/></div></div><div className="engine-card"><div className="engine-heading"><div className="engine-symbol"><Cpu size={21}/></div><div><strong>Ollama Engine</strong><small>{health?.models[0] ?? "Chưa phát hiện model"}</small></div><span className={`engine-status ${health?.ollama === "online" ? "good" : "bad"}`}>{health?.ollama === "online" ? "ONLINE" : "OFFLINE"}</span></div><div className="engine-line"/><div className="engine-caption">{health?.ollama === "online" ? `${models.length} model sẵn sàng · chạy local` : "Mở Ollama và tải model bằng ollama pull"}</div></div><div className="workflow"><h4>Quy trình tạo bài học</h4><div className="workflow-step"><span>01</span><div><strong>Nhập chủ đề hoặc tài liệu</strong><small>PDF · Markdown · TXT</small></div><CheckCircle2 size={17}/></div><div className="workflow-step"><span>02</span><div><strong>Duyệt dàn ý trước khi tạo bài</strong><small>Chỉnh dàn ý · tạo từng slide · lưu tiến độ</small></div><CheckCircle2 size={17}/></div><div className="workflow-step"><span>03</span><div><strong>Học qua tương tác</strong><small>Quiz · thẻ nhớ · Harris Lab</small></div><CheckCircle2 size={17}/></div></div><button className="btn btn-studio" onClick={() => setModal(true)}><Plus size={17}/> Tạo lớp học mới <ArrowRight size={17}/></button></section></div>
      <footer className="page-footer"><span>© OpenClass AI · Local-first Learning Studio</span><span>Built with Next.js · FastAPI · Ollama · PostgreSQL</span></footer>
    </div><CreateLessonModal open={modal} onClose={() => setModal(false)} availableModels={models}/>
  </Shell>;
}
