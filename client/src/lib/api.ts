import axios from "axios";
import type {
  ChatAnswer,
  ChatHistoryItem,
  DashboardStats,
  PaperAnalysis,
  PaperSummary,
  PaperUploadResponse,
  SearchResponse,
  StudyNotes,
} from "@/types";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: { Accept: "application/json" },
});

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (error.message) return error.message;
  }
  return "Something went wrong. Please try again.";
}

// --- Papers ---
export const papersApi = {
  upload: async (file: File, onProgress?: (pct: number) => void): Promise<PaperUploadResponse> => {
    const form = new FormData();
    form.append("file", file);
    const { data } = await apiClient.post<PaperUploadResponse>("/papers/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (evt) => {
        if (onProgress && evt.total) onProgress(Math.round((evt.loaded / evt.total) * 100));
      },
    });
    return data;
  },
  uploadMultiple: async (files: File[]): Promise<PaperUploadResponse[]> => {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    const { data } = await apiClient.post<PaperUploadResponse[]>("/papers/upload-multiple", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },
  list: async (): Promise<PaperSummary[]> => (await apiClient.get("/papers")).data,
  get: async (id: string): Promise<PaperAnalysis> => (await apiClient.get(`/papers/${id}`)).data,
  getStatus: async (id: string) => (await apiClient.get(`/papers/${id}/status`)).data as {
    id: string;
    status: string;
    error_message: string | null;
  },
  toggleFavorite: async (id: string, isFavorite: boolean): Promise<PaperSummary> =>
    (await apiClient.patch(`/papers/${id}/favorite`, { is_favorite: isFavorite })).data,
  updateProgress: async (id: string, percent: number): Promise<PaperSummary> =>
    (await apiClient.patch(`/papers/${id}/progress`, { reading_progress_percent: percent })).data,
  markOpened: async (id: string): Promise<PaperSummary> => (await apiClient.post(`/papers/${id}/open`)).data,
  remove: async (id: string): Promise<void> => {
    await apiClient.delete(`/papers/${id}`);
  },
};

// --- Chat / RAG ---
export const chatApi = {
  ask: async (paperId: string, question: string): Promise<ChatAnswer> =>
    (await apiClient.post(`/chat/${paperId}/ask`, { question })).data,
  history: async (paperId: string): Promise<ChatAnswer[]> => (await apiClient.get(`/chat/${paperId}/history`)).data,
  allHistory: async (): Promise<ChatHistoryItem[]> => (await apiClient.get("/chat/history/all")).data,
};

// --- Study Notes ---
export const notesApi = {
  generate: async (paperId: string): Promise<StudyNotes> => (await apiClient.post(`/notes/${paperId}/generate`)).data,
  get: async (paperId: string): Promise<StudyNotes | null> => {
    try {
      return (await apiClient.get(`/notes/${paperId}`)).data;
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 404) return null;
      throw err;
    }
  },
};

// --- Search ---
export const searchApi = {
  searchAll: async (query: string, topK = 8): Promise<SearchResponse> =>
    (await apiClient.post("/search", { query, top_k: topK })).data,
  searchInPaper: async (paperId: string, query: string, topK = 8): Promise<SearchResponse> =>
    (await apiClient.post(`/search/${paperId}`, { query, top_k: topK })).data,
};

// --- Dashboard ---
export const dashboardApi = {
  get: async (): Promise<DashboardStats> => (await apiClient.get("/dashboard")).data,
};

// --- Export ---
export const exportApi = {
  downloadUrl: (paperId: string, kind: "summary" | "study-notes" | "flashcards") =>
    `${API_BASE}/api/v1/export/${paperId}/${kind}`,
};
