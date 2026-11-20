# OpenClass AI

**Local-first interactive lessons from your documents.**
**Biến tài liệu thành bài học tương tác bằng AI chạy trên máy của bạn.**

OpenClass AI v0.2 · Next.js · React · TypeScript · FastAPI · PostgreSQL · Ollama · [MIT License](LICENSE)

[Features / Tính năng](#features) · [Setup / Cài đặt](#setup) · [Reopen / Mở lại](#reopen) · [Usage / Sử dụng](#usage) · [Reference / Tham chiếu](#reference)

## Overview / Giới thiệu

**EN:** Turn a topic or up to five PDF, Markdown, or TXT documents into a Vietnamese lesson with slides, a quiz, and flashcards. Review the outline, inspect source excerpts, and edit individual slides. Inference runs through local Ollama; no paid AI API is required. The interface and generated teaching content are currently in Vietnamese; this README is bilingual.

**VI:** Biến chủ đề hoặc tối đa năm tài liệu PDF, Markdown, TXT thành bài học tiếng Việt gồm slide, quiz và flashcards. Bạn duyệt dàn ý, xem đoạn nguồn và chỉnh từng slide. AI chạy qua Ollama local, không cần API AI trả phí. Giao diện và bài giảng hiện dùng tiếng Việt; README này có cả tiếng Anh và tiếng Việt.

<a id="features"></a>
## Features / Tính năng

| English | Tiếng Việt |
|---|---|
| Review and edit the outline before generating slides. | Duyệt và sửa dàn ý trước khi tạo slide. |
| Fast mode recommends `qwen2.5:3b`; Balanced mode recommends `qwen3:4b`. Select other installed local text-generation models too. | Chế độ Nhanh đề xuất `qwen2.5:3b`, Cân bằng đề xuất `qwen3:4b`; có thể chọn model tạo văn bản local khác đã cài. |
| Check availability and capabilities; reject embedding-only and detected cloud models. | Kiểm tra model đã cài và khả năng tạo văn bản; chặn model chỉ embedding và model được xác định là cloud. |
| Select, drag and drop, add, or remove multiple documents before submission. | Chọn, kéo thả, thêm nhiều lần hoặc xóa từng tài liệu trước khi gửi. |
| Save full extracted text by page in PostgreSQL; retrieve relevant excerpts for each slide. | Lưu đầy đủ văn bản trích xuất theo trang trong PostgreSQL; tìm đoạn liên quan cho từng slide. |
| Inspect filenames, PDF page numbers, and excerpts used to draft a slide. | Đối chiếu tên file, số trang PDF và đoạn trích dùng để soạn slide. |
| Save each completed slide and resume an unfinished step after failure. | Lưu từng slide hoàn tất và tiếp tục phần đang dở sau lỗi. |
| Edit or regenerate one slide while retaining the others. | Chỉnh hoặc tạo lại riêng một slide, giữ các slide còn lại. |
| Three quiz questions, three flashcards, and a Harris lab for Harris-related lessons. | Ba câu quiz, ba flashcards và Harris Lab cho bài liên quan Harris Corner Detection. |
| Open an offline sample without running a model. | Mở bài mẫu offline mà không cần chạy model. |

<a id="setup"></a>
## First-time setup / Cài lần đầu

### Requirements / Yêu cầu

**EN:** The documented local setup uses Windows 11, Docker Desktop with Docker Compose, Python 3.11+ (3.12 is a suitable starting point), Node.js 22+, npm, Git, and Ollama. Start with small models on a 16 GB RAM / 4 GB GPU machine; actual speed and memory use depend on the model, context, and other applications.

**VI:** Hướng dẫn này dành cho Windows 11, Docker Desktop có Docker Compose, Python từ 3.11 (có thể bắt đầu với 3.12), Node.js từ 22, npm, Git và Ollama. Với máy 16 GB RAM / GPU 4 GB VRAM, nên bắt đầu bằng model nhỏ; tốc độ và bộ nhớ thực tế phụ thuộc model, context và ứng dụng đang mở.

### 1. Get the source / Tải mã nguồn

```powershell
git clone https://github.com/HoangThongTom/OpenClass-AI.git
cd OpenClass-AI
```

### 2. Start Ollama and PostgreSQL / Mở Ollama và PostgreSQL

**EN:** Open Docker Desktop and Ollama. From the project root, download the default model and start the database. Downloading is only needed when the model is not already installed.

**VI:** Mở Docker Desktop và Ollama. Từ thư mục gốc dự án, tải model mặc định và khởi động database. Chỉ cần tải model nếu máy chưa có.

```powershell
ollama pull qwen2.5:3b
ollama list
docker compose up -d db
```

**EN:** Optional Balanced model: `ollama pull qwen3:4b`.

**VI:** Tùy chọn cho chế độ Cân bằng: `ollama pull qwen3:4b`.

### 3. Backend / Chạy backend

**EN:** Open a second PowerShell window at the project root, then run the commands below. The conditional copy preserves an existing `.env`. Keep this terminal open.

**VI:** Mở PowerShell thứ hai tại thư mục gốc, rồi chạy các lệnh bên dưới. Lệnh sao chép có điều kiện giữ nguyên `.env` đã có. Giữ cửa sổ này đang mở.

```powershell
cd backend
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
if (-not (Test-Path .venv\Scripts\python.exe)) { py -3 -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**EN:** When started inside `backend/`, the API reads `backend/.env`. Startup creates missing tables; v0.2 adds document and workspace tables without replacing saved lessons.

**VI:** Khi chạy từ `backend/`, API đọc `backend/.env`. Lúc khởi động, API tự tạo bảng còn thiếu; v0.2 thêm bảng tài liệu và tiến độ, không thay thế bài học đã lưu.

### 4. Frontend / Chạy giao diện

**EN:** Open a third PowerShell window at the project root. Install dependencies and keep the development server running.

**VI:** Mở PowerShell thứ ba tại thư mục gốc. Cài thư viện và giữ máy chủ giao diện đang chạy.

```powershell
cd frontend
npm ci
npm run dev
```

Open / Truy cập: **[OpenClass AI — localhost:3002](http://localhost:3002)**.
API documentation / Tài liệu API: **[127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**.

<a id="reopen"></a>
## Reopen an existing installation / Mở lại sau khi đã cài

**EN:** Start Docker Desktop and Ollama, then run each command in a separate PowerShell window from the indicated directory. There is no need to recreate `.env` or reinstall dependencies on every launch. Stop an old backend/frontend process with **Ctrl+C** before restarting it.

**VI:** Mở Docker Desktop và Ollama, rồi chạy mỗi lệnh trong một cửa sổ PowerShell riêng, từ thư mục tương ứng. Không cần tạo lại `.env` hoặc cài lại thư viện mỗi lần mở. Nếu backend/frontend cũ còn chạy, nhấn **Ctrl+C** trước khi chạy lại.

| Directory / Thư mục | Command / Lệnh |
|---|---|
| Project root / Gốc dự án | `docker compose up -d db` |
| `backend/` | `.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000` |
| `frontend/` | `npm run dev` |

Then open / Sau đó truy cập **[localhost:3002](http://localhost:3002)**.

**EN:** To stop, press **Ctrl+C** in the backend/frontend terminals. `docker compose down` from the project root stops Compose services and keeps the database volume. **Do not add `-v` if you want to preserve lessons; that option deletes the database volume.**

**VI:** Để tắt, nhấn **Ctrl+C** ở cửa sổ backend/frontend. `docker compose down` từ thư mục gốc dừng các dịch vụ Compose và giữ volume database. **Không thêm `-v` nếu muốn giữ bài học; tùy chọn đó xóa volume database.**

<a id="usage"></a>
## Usage / Sử dụng

| Step | English | Tiếng Việt |
|---|---|---|
| 1 | Click **Tạo bài học** or **Tạo lớp mới**; enter a title and topic, optionally attach documents. | Nhấn **Tạo bài học** hoặc **Tạo lớp mới**, nhập tên/chủ đề và đính kèm tài liệu nếu cần. |
| 2 | Choose a mode, an installed model, and **2–6 slides**. | Chọn chế độ, model đã cài và **2–6 slide**. |
| 3 | Click **Tạo dàn ý để duyệt**, edit the outline, then **Duyệt và tạo bài học**. | Nhấn **Tạo dàn ý để duyệt**, chỉnh các mục rồi **Duyệt và tạo bài học**. |
| 4 | Follow the saved slide count. Use **Tiếp tục phần đang dở** after failure; **Tạo dàn ý mới** restarts from the outline. | Theo dõi số slide đã lưu. Khi lỗi dùng **Tiếp tục phần đang dở**; **Tạo dàn ý mới** sẽ bắt đầu lại từ dàn ý. |
| 5 | Inspect sources below a slide. Use **Chỉnh slide này** or **AI tạo lại slide này** to improve it. | Mở nguồn dưới slide để đối chiếu. Dùng **Chỉnh slide này** hoặc **AI tạo lại slide này** để cải thiện riêng slide đó. |
| 6 | Take the quiz, flip flashcards, or open Harris Lab when available. | Làm quiz, lật flashcards hoặc mở Harris Lab nếu có. |

**EN:** Editing or regenerating a single slide retains the quiz and flashcards. Review their consistency if you change the lesson's facts. Source references show excerpts used to draft the slide; they do not guarantee every generated statement is accurate.

**VI:** Khi sửa hoặc tạo lại riêng một slide, quiz/flashcards được giữ nguyên. Cần đối chiếu lại nếu thay đổi kiến thức. Dẫn nguồn cho biết đoạn tài liệu dùng để soạn slide, không bảo đảm mọi diễn giải AI đều đúng.

## Docker alternative / Chạy toàn bộ bằng Docker

```powershell
docker compose up --build -d
```

**EN:** Run from the project root. This builds and starts the database, API, and web interface. Containerized API access to host Ollama uses `host.docker.internal:11434`; Docker Desktop must be able to reach that service. The web address remains [localhost:3002](http://localhost:3002). The root [.env.example](.env.example) documents `OLLAMA_MODEL` for Compose; preserve any existing root `.env`.

**VI:** Chạy từ thư mục gốc để build và khởi động database, API, giao diện. API trong container kết nối Ollama trên máy qua `host.docker.internal:11434`; Docker Desktop phải truy cập được dịch vụ đó. Giao diện vẫn ở [localhost:3002](http://localhost:3002). File [.env.example](.env.example) ở gốc mô tả `OLLAMA_MODEL` cho Compose; giữ nguyên `.env` đã có khi cấu hình.

<a id="reference"></a>
## Technical reference / Tham chiếu kỹ thuật

### Limits / Giới hạn

| Setting / Thiết lập | Value / Giá trị |
|---|---|
| Slides / Số slide | 2–6 |
| Documents / Số tài liệu | Up to / Tối đa 5 |
| Per file / Mỗi file | 15 MB by default / mặc định |
| Total upload / Tổng upload | 30 MB |
| Extracted text per file / Văn bản mỗi file | 2,000,000 characters / ký tự |
| Extracted text per lesson / Văn bản mỗi bài | 5,000,000 characters / ký tự |
| Default context / Context mặc định | 4,096 tokens |
| Outline source budget / Đoạn nguồn cho dàn ý | Up to / Tối đa 2,400 characters by default / ký tự mặc định |
| Slide source budget / Đoạn nguồn cho slide | Up to / Tối đa 2,200 characters; also respects / đồng thời tuân theo `OLLAMA_SOURCE_CHAR_LIMIT` |

**EN:** The 8,500-character `lessons.source_text` field is a compatibility preview. Full new text is stored separately in `lesson_documents`, subject to the limits above; exceeding extraction limits produces an error rather than silently truncating full documents. PDF text extraction reads all pages; original PDF binaries are not stored. Markdown/TXT references do not have original page numbers.

**VI:** Trường `lessons.source_text` giới hạn 8.500 ký tự là bản xem trước để tương thích. Văn bản mới đầy đủ nằm trong `lesson_documents`, trong các giới hạn trên; khi vượt giới hạn trích xuất, ứng dụng báo lỗi thay vì âm thầm cắt tài liệu. PDF được trích xuất văn bản ở mọi trang, không lưu file PDF nhị phân gốc. Markdown/TXT không có số trang gốc.

### Configuration / Cấu hình

Template / File mẫu: [backend/.env.example](backend/.env.example).

| Variable / Biến | Default / Mặc định | Purpose / Ý nghĩa |
|---|---|---|
| `DATABASE_URL` | See template / Xem file mẫu | PostgreSQL connection / Kết nối PostgreSQL |
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama endpoint / Địa chỉ Ollama |
| `DEFAULT_OLLAMA_MODEL` | `qwen2.5:3b` | Default local model / Model local mặc định |
| `OLLAMA_TIMEOUT_SECONDS` | `600` | HTTP timeout / Thời gian chờ HTTP |
| `OLLAMA_NUM_CTX` | `4096` | Context, allowed / cho phép 4096–32768 |
| `OLLAMA_SOURCE_CHAR_LIMIT` | `2400` | Excerpt budget, allowed / giới hạn đoạn trích, cho phép 500–8500 |
| `MAX_UPLOAD_MB` | `15` | Per-file upload limit / Giới hạn upload mỗi file |

Ports / Cổng: frontend **3002**, API **8000**, PostgreSQL host **5434**, Ollama **11434**. Compose uses root `OLLAMA_MODEL`; the locally run backend uses `DEFAULT_OLLAMA_MODEL`. / Compose dùng `OLLAMA_MODEL` ở gốc; backend chạy trực tiếp dùng `DEFAULT_OLLAMA_MODEL`.

### API

| Method | Endpoint | Purpose / Chức năng |
|---|---|---|
| GET | `/api/health` | Service status / Trạng thái dịch vụ |
| GET | `/api/models` | Installed model names / Model đã cài |
| GET | `/api/model-info?model=qwen3:4b` | Local generation capability / Khả năng tạo văn bản local |
| GET | `/api/lessons` | Lesson library / Thư viện bài học |
| GET | `/api/lessons/{id}` | Lesson and progress / Bài học và tiến độ |
| POST | `/api/lessons` | Create an outline job / Bắt đầu tạo dàn ý |
| POST | `/api/lessons/{id}/generate` | Restart with optional model, slide_count, mode / Tạo lại với lựa chọn mới |
| PUT | `/api/lessons/{id}/outline` | Save an edited outline / Lưu dàn ý đã sửa |
| POST | `/api/lessons/{id}/approve` | Approve and generate / Duyệt và tạo bài |
| POST | `/api/lessons/{id}/resume` | Resume a failed job / Tiếp tục phần lỗi |
| PATCH | `/api/lessons/{id}/slides/{index}` | Edit one slide / Sửa một slide |
| POST | `/api/lessons/{id}/slides/{index}/generate` | Regenerate one slide / Tạo lại một slide |
| DELETE | `/api/lessons/{id}` | Delete a lesson / Xóa bài học |
| POST | `/api/demo` | Create the offline Harris sample / Tạo bài Harris mẫu |

**EN:** Creation accepts multipart fields `title`, `topic`, `model`, `slide_count`, `mode` (`fast` or `balanced`), and repeated `files`. The legacy single-file field `file` is accepted. Outline save/approval takes JSON `{summary, slides: [{title, focus}]}`. Slide indices start at zero. Background-job endpoints return **202 Accepted**; poll lesson details for progress.

**VI:** Tạo bài nhận multipart gồm `title`, `topic`, `model`, `slide_count`, `mode` (`fast` hoặc `balanced`) và danh sách `files`; vẫn nhận `file` đơn từ bản cũ. Lưu/duyệt dàn ý dùng JSON `{summary, slides: [{title, focus}]}`. Chỉ số slide bắt đầu từ 0. Endpoint tác vụ nền trả **202 Accepted**; lấy chi tiết bài học để theo dõi tiến độ.

Statuses / Trạng thái: `generating` → `draft` (outline review / chờ duyệt) → `generating` → `ready`; errors use / khi lỗi dùng `failed`.

### Tests and benchmark / Kiểm thử và đo tốc độ

From `backend/` / Từ thư mục `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

From `frontend/` / Từ thư mục `frontend/`:

```powershell
npm test
npm run lint
npm run build
```

**EN:** Backend tests use in-memory SQLite and mocked Ollama; they do not write the user's PostgreSQL. To benchmark both suggested installed models, run from the project root:

**VI:** Test backend dùng SQLite trong bộ nhớ và Ollama giả lập, không ghi PostgreSQL của người dùng. Để đo cả hai model đề xuất đã cài, chạy từ thư mục gốc:

```powershell
backend\.venv\Scripts\python.exe -X utf8 scripts/benchmark-models.py
```

**EN:** The benchmark uses the public Harris example, real local inference, and in-memory SQLite. [Recorded results](reports/local-model-benchmark.json): a four-slide run took **35.90 s** with `qwen2.5:3b` and **100.24 s** with `qwen3:4b`; both returned 4 slides, 3 quiz items, 3 flashcards, and cited excerpts for every slide. These are sample measurements, not speed guarantees or a factual-quality evaluation.

**VI:** Phép đo dùng bài Harris mẫu, model local thật và SQLite trong bộ nhớ. [Kết quả đã lưu](reports/local-model-benchmark.json): lượt đo 4 slide mất **35,90 giây** với `qwen2.5:3b`, **100,24 giây** với `qwen3:4b`; cả hai đủ 4 slide, 3 quiz, 3 flashcards và nguồn cho từng slide. Đây là số đo tham khảo, không phải cam kết tốc độ hay đánh giá độ chính xác kiến thức.

### Troubleshooting / Xử lý lỗi

| Symptom / Hiện tượng | Action / Cách xử lý |
|---|---|
| Website unavailable / Không mở được web | Keep `npm run dev` running; check port 3002 / Giữ frontend chạy, kiểm tra cổng 3002 |
| API unavailable / Không kết nối API | Check the backend terminal and `/docs` / Kiểm tra cửa sổ backend và `/docs` |
| Database connection error / Lỗi database | Start Docker Desktop and `docker compose up -d db`; check port 5434 / Mở Docker và PostgreSQL, kiểm tra cổng 5434 |
| No models / Không có model | Start Ollama, run `ollama list`, download a local model / Mở Ollama, kiểm tra và tải model local |
| Timeout or token limit / Quá thời gian hoặc hết token | Resume; if repeated, simplify the outline or choose another small model / Tiếp tục; nếu lặp lại, rút gọn dàn ý hoặc đổi model nhỏ |
| Slow generation / Tạo bài chậm | Inspect `ollama ps` and API timings / Xem `ollama ps` và thời gian trong log API |
| Scanned or locked PDF / PDF scan hoặc có mật khẩu | Use a text-based, unlocked PDF or Markdown / Dùng PDF có văn bản, đã mở khóa, hoặc Markdown |

**EN:** Logs include the lesson ID, model, step, token counts, and load/prompt/generation timings. Document text is not intentionally logged.

**VI:** Log ghi ID bài, model, bước, token và thời gian tải/xử lý/sinh. Không chủ động ghi văn bản tài liệu.

### Current limitations / Giới hạn hiện tại

| English | Tiếng Việt |
|---|---|
| Scanned PDFs need OCR, which is not implemented. | PDF scan cần OCR, tính năng này chưa có. |
| Retrieval uses local keyword scoring with Vietnamese normalization, not semantic embeddings. | Tìm đoạn bằng từ khóa có chuẩn hóa tiếng Việt, chưa dùng embedding ngữ nghĩa. |
| Older truncated text cannot be recovered without uploading original files in a new lesson. | Cần tải file gốc trong bài mới để lấy lại phần văn bản từng bị cắt ở bản cũ. |
| Use one API worker. Checkpoints survive restarts, but jobs run inside the API process and require explicit resume after interruption. | Chạy một API worker. Tiến độ còn sau khi khởi động lại, nhưng tác vụ chạy trong process API và cần nhấn tiếp tục sau gián đoạn. |
| No authentication or production multi-user isolation; the documented deployment is for localhost. | Chưa có đăng nhập hoặc cô lập dữ liệu nhiều người dùng; cách triển khai được hướng dẫn dành cho localhost. |
| No PPTX/PDF export, speech, video, or automatic general-purpose simulations. Harris Lab uses illustrative values rather than detecting corners from an uploaded image. | Chưa xuất PPTX/PDF, giọng nói, video hoặc mô phỏng tự động mọi chủ đề. Harris Lab dùng số minh họa, không phát hiện góc từ ảnh tải lên. |

### Project layout / Cấu trúc dự án

```text
OpenClass-AI/
├── backend/
│   ├── app/
│   │   ├── main.py          # API
│   │   ├── workflow.py      # Outline review and checkpoints / Dàn ý và tiến độ
│   │   ├── retrieval.py     # Local excerpt search / Tìm đoạn nguồn
│   │   ├── parser.py        # Full-text extraction / Trích xuất văn bản
│   │   ├── ollama.py        # Model inspection and structured generation
│   │   ├── models.py        # Lessons, documents, workspaces
│   │   ├── schemas.py
│   │   ├── config.py
│   │   ├── db.py
│   │   └── demo.py
│   ├── tests/
│   └── .env.example
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── tests/
├── examples/harris-corner-detection.md
├── reports/local-model-benchmark.json
├── scripts/benchmark-models.py
├── scripts/start-windows.ps1
├── docker-compose.yml
└── README.md
```

### License and data / Giấy phép và dữ liệu

**EN:** Project source uses the [MIT License](LICENSE). Model weights have their own licenses. This independent project is not affiliated with THU-MAIC or OpenMAIC. Keep `.env`, credentials, private documents, databases, `.venv`, `node_modules`, and generated build/test artifacts out of Git. Templates named `.env.example` are intended for version control.

**VI:** Mã nguồn dùng [giấy phép MIT](LICENSE); trọng số model có giấy phép riêng. Dự án độc lập, không liên kết THU-MAIC hoặc OpenMAIC. Không đưa `.env`, thông tin đăng nhập, tài liệu riêng, database, `.venv`, `node_modules` và dữ liệu build/test lên Git. File mẫu `.env.example` được phép lưu trong repo.
