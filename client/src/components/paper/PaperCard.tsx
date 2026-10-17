import { Link } from "react-router-dom";
import { FileText, Star, Calendar, Layers } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/paper/StatusBadge";
import { Progress } from "@/components/ui/Progress";
import { formatDate, cn } from "@/lib/utils";
import type { PaperSummary } from "@/types";

export function PaperCard({
  paper,
  onToggleFavorite,
}: {
  paper: PaperSummary;
  onToggleFavorite?: (id: string, next: boolean) => void;
}) {
  return (
    <Card className="p-0 overflow-hidden hover:shadow-md transition-shadow">
      <Link to={`/papers/${paper.id}`} className="block p-5">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start gap-3 min-w-0">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
              <FileText className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <h3 className="font-display font-semibold leading-snug truncate">
                {paper.title || paper.original_filename}
              </h3>
              <div className="flex items-center gap-3 mt-1 text-xs text-[var(--color-ink-soft)]">
                <span className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" /> {formatDate(paper.created_at)}
                </span>
                {paper.total_pages > 0 && (
                  <span className="flex items-center gap-1">
                    <Layers className="h-3 w-3" /> {paper.total_pages} pages
                  </span>
                )}
              </div>
            </div>
          </div>
          <button
            onClick={(e) => {
              e.preventDefault();
              onToggleFavorite?.(paper.id, !paper.is_favorite);
            }}
            className="shrink-0 rounded-md p-1.5 hover:bg-[var(--color-surface-2)]"
            aria-label={paper.is_favorite ? "Remove from favorites" : "Add to favorites"}
          >
            <Star
              className={cn(
                "h-4 w-4",
                paper.is_favorite ? "fill-[var(--color-warning)] text-[var(--color-warning)]" : "text-[var(--color-ink-soft)]"
              )}
            />
          </button>
        </div>

        <div className="mt-4 flex items-center justify-between gap-3">
          <StatusBadge status={paper.status} />
          {paper.status === "ready" && paper.reading_progress_percent > 0 && (
            <div className="flex items-center gap-2 flex-1 max-w-[100px]">
              <Progress value={paper.reading_progress_percent} className="h-1.5" />
              <span className="text-xs text-[var(--color-ink-soft)] shrink-0">{paper.reading_progress_percent}%</span>
            </div>
          )}
        </div>
      </Link>
    </Card>
  );
}
