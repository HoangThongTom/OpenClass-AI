export type LessonStatus = "draft" | "generating" | "ready" | "failed";

export interface Slide {
  title: string;
  key_point: string;
  bullets: string[];
  speaker_notes: string;
  sources?: { document_id: string; filename: string; page: number | null; excerpt: string }[];
}
export type GenerationMode = "fast" | "balanced";
export interface Outline { summary: string; slides: { title: string; focus: string }[] }
export interface Workspace {
  mode: GenerationMode; outline: Outline | null; stage: string; approved: boolean;
  completed_slides: number; elapsed_seconds: number; last_run_seconds: number; source_warning: string | null;
}
export interface QuizItem {
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
}
export interface Flashcard {
  front: string;
  back: string;
}
export interface LessonContent {
  summary: string;
  slides: Slide[];
  quiz: QuizItem[];
  flashcards: Flashcard[];
}
export interface Lesson {
  id: string;
  title: string;
  topic: string;
  model: string;
  slide_count: number;
  status: LessonStatus;
  source_name: string | null;
  created_at: string;
  content: LessonContent | null;
  error: string | null;
  workspace?: Workspace | null;
}
export interface Health {
  api: string;
  database: string;
  ollama: string;
  models: string[];
}
export interface Models {
  online: boolean;
  models: string[];
  error: string | null;
}
