import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function formatDateTime(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function truncate(text: string, max = 140): string {
  if (text.length <= max) return text;
  return text.slice(0, max).trim() + "…";
}

export function confidenceLabel(score: number): { label: string; tone: "high" | "medium" | "low" } {
  if (score >= 0.75) return { label: "High confidence", tone: "high" };
  if (score >= 0.4) return { label: "Medium confidence", tone: "medium" };
  return { label: "Low confidence", tone: "low" };
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
