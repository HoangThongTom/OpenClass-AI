"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowUpRight, Blocks, BookOpenText, GraduationCap, LayoutDashboard, Monitor, Sparkles } from "lucide-react";

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link href="/" className="brand">
          <span className="brand-icon"><GraduationCap size={22} strokeWidth={2.5} /></span>
          <span className="brand-name">openclass<span className="brand-dot">.</span><small>AI LEARNING STUDIO</small></span>
        </Link>
        <div className="nav-label">WORKSPACE</div>
        <nav className="navigation">
          <Link href="/" className={`nav-item ${pathname === "/" ? "active" : ""}`}><LayoutDashboard size={19} /> Tổng quan</Link>
          <Link href="/#library" className="nav-item"><BookOpenText size={19} /> Thư viện bài học</Link>
        </nav>
        <div className="nav-label second-label">CÔNG CỤ</div>
        <nav className="navigation">
          <Link href="/#studio" className="nav-item"><Sparkles size={19} /> AI Studio <span className="nav-hint">NEW</span></Link>
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" className="nav-item"><Blocks size={19} /> API Explorer <ArrowUpRight size={14} className="ml-auto" /></a>
        </nav>
        <div className="sidebar-spacer" />
        <div className="sidebar-bottom-card">
          <span className="mini-icon"><Monitor size={18} /></span>
          <strong>Local-first workspace</strong>
          <p>Bài học lưu trên máy. Model chạy qua Ollama, không cần API trả phí.</p>
          <div className="online-caption"><span className="online-dot" /> COMMUNITY EDITION</div>
        </div>
        <div className="sidebar-footer"><span className="avatar">OC</span><span><b>My Workspace</b><small>Developer • Local</small></span><span className="footer-ellipsis">•••</span></div>
      </aside>
      <main className="main-content">{children}</main>
    </div>
  );
}
