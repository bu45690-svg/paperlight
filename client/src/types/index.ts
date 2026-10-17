export type PaperStatus =
  | "uploaded"
  | "extracting"
  | "analyzing"
  | "indexing"
  | "ready"
  | "failed";

export interface PaperSummary {
  id: string;
  original_filename: string;
  title: string | null;
  status: PaperStatus;
  total_pages: number;
  is_favorite: boolean;
  reading_progress_percent: number;
  created_at: string;
}

export interface PaperAnalysis {
  id: string;
  original_filename: string;
  title: string | null;
  status: PaperStatus;
  error_message: string | null;
  total_pages: number;
  executive_summary: string | null;
  abstract_summary: string | null;
  key_contributions: string[] | null;
  methodology: string | null;
  results: string | null;
  limitations: string | null;
  future_work: string | null;
  keywords: string[] | null;
  important_equations: string[] | null;
  important_figures: string[] | null;
  references_count: number;
  is_favorite: boolean;
  reading_progress_percent: number;
  created_at: string;
  updated_at: string;
}

export interface ChatAnswer {
  id: string;
  question: string;
  answer: string;
  page_numbers: number[] | null;
  citations: string[] | null;
  confidence_score: number;
  created_at: string;
}

export interface ChatHistoryItem extends ChatAnswer {
  paper_id: string;
  paper_title: string | null;
}

export interface Flashcard {
  question: string;
  answer: string;
}

export interface MCQ {
  question: string;
  options: string[];
  correct_answer_index: number;
  explanation?: string;
}

export interface StudyNotes {
  id: string;
  paper_id: string;
  exam_notes: string[] | null;
  flashcards: Flashcard[] | null;
  bullet_notes: string[] | null;
  interview_questions: string[] | null;
  viva_questions: string[] | null;
  mcqs: MCQ[] | null;
}

export interface SearchResultItem {
  paper_id: string;
  paper_title: string | null;
  page_number: number | null;
  snippet: string;
  score: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResultItem[];
}

export interface DashboardStats {
  total_papers: number;
  total_pages: number;
  total_chat_messages: number;
  recent_uploads: PaperSummary[];
  favorite_papers: PaperSummary[];
}

export interface PaperUploadResponse {
  id: string;
  filename: string;
  status: PaperStatus;
  message: string;
}

export interface ApiErrorBody {
  detail: string;
}
