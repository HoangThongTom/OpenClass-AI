import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OpenClass AI · Biến tài liệu thành lớp học",
  description: "Nền tảng tạo bài giảng tương tác local-first với Ollama, FastAPI và PostgreSQL.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="vi"><body>{children}</body></html>;
}
