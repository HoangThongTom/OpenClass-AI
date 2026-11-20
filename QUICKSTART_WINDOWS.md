# Windows quickstart / Mở nhanh trên Windows

The current English–Vietnamese setup guide is in [README.md](README.md#setup).
Hướng dẫn cài đặt Anh–Việt hiện tại nằm trong [README.md](README.md#setup).

For an existing installation, start Docker Desktop and Ollama, then run these commands in separate PowerShell windows.
Nếu đã cài, mở Docker Desktop và Ollama, rồi chạy các lệnh sau ở các cửa sổ PowerShell riêng.

| Directory / Thư mục | Command / Lệnh |
|---|---|
| Project root / Gốc dự án | `docker compose up -d db` |
| `backend/` | `.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000` |
| `frontend/` | `npm run dev` |

Open / Truy cập: [localhost:3002](http://localhost:3002).

Keep the backend/frontend terminals open. Preserve your existing `.env` and database volume.
Giữ hai cửa sổ backend/frontend đang mở. Giữ nguyên `.env` và volume database đã có.

For the v0.2 outline approval, source references, and resume workflow, see [Usage / Sử dụng](README.md#usage).
Xem [Usage / Sử dụng](README.md#usage) để dùng dàn ý, dẫn nguồn và tiếp tục phần lỗi của v0.2.
