import * as React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Star, Download, Trash2, ArrowLeft } from "lucide-react";
import { PageHeader } from "@/components/layout/AppLayout";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/Tabs";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/paper/StatusBadge";
import { OverviewTab } from "@/components/paper/OverviewTab";
import { ChatTab } from "@/components/paper/ChatTab";
import { StudyNotesTab } from "@/components/paper/StudyNotesTab";
import { papersApi, exportApi } from "@/lib/api";
import { usePaperStatusPolling } from "@/hooks/usePaperStatusPolling";
import { useToast } from "@/components/ui/Toast";
import { cn } from "@/lib/utils";
import type { PaperAnalysis } from "@/types";

export default function PaperDetailPage() {
  const { paperId } = useParams<{ paperId: string }>();
  const navigate = useNavigate();
  const { push } = useToast();
  const [paper, setPaper] = React.useState<PaperAnalysis | null>(null);
  const [loading, setLoading] = React.useState(true);

  const load = React.useCallback(async () => {
    if (!paperId) return;
    try {
      const data = await papersApi.get(paperId);
      setPaper(data);
    } catch {
      push({ kind: "error", title: "Couldn't load paper" });
    } finally {
      setLoading(false);
    }
  }, [paperId, push]);

  React.useEffect(() => {
    load();
    if (paperId) papersApi.markOpened(paperId).catch(() => {});
  }, [load, paperId]);

  const { status } = usePaperStatusPolling(paperId, paper?.status, load);

  const toggleFavorite = async () => {
    if (!paperId || !paper) return;
    const updated = await papersApi.toggleFavorite(paperId, !paper.is_favorite);
    setPaper((p) => (p ? { ...p, is_favorite: updated.is_favorite } : p));
  };

  const deletePaper = async () => {
    if (!paperId) return;
    if (!confirm("Delete this paper and all its chat history and study notes? This can't be undone.")) return;
    await papersApi.remove(paperId);
    push({ kind: "success", title: "Paper deleted" });
    navigate("/");
  };

  if (!paperId) return null;

  const isReady = status === "ready";

  return (
    <div>
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-1 text-sm text-[var(--color-ink-soft)] hover:text-[var(--color-ink)] mb-4"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back
      </button>

      <PageHeader
        title={paper?.title || paper?.original_filename || "Loading…"}
        description={status ? undefined : undefined}
        actions={
          <>
            <StatusBadge status={status ?? "uploaded"} />
            <Button variant="outline" size="icon" onClick={toggleFavorite} aria-label="Toggle favorite">
              <Star className={cn("h-4 w-4", paper?.is_favorite && "fill-[var(--color-warning)] text-[var(--color-warning)]")} />
            </Button>
            {isReady && (
              <a href={exportApi.downloadUrl(paperId, "summary")}>
                <Button variant="secondary" size="icon" aria-label="Export summary as PDF">
                  <Download className="h-4 w-4" />
                </Button>
              </a>
            )}
            <Button variant="outline" size="icon" onClick={deletePaper} aria-label="Delete paper">
              <Trash2 className="h-4 w-4" />
            </Button>
          </>
        }
      />

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="chat">AI Chat</TabsTrigger>
          <TabsTrigger value="notes">Study Notes</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <OverviewTab paper={paper} loading={loading} />
        </TabsContent>
        <TabsContent value="chat">
          <ChatTab paperId={paperId} isReady={isReady} />
        </TabsContent>
        <TabsContent value="notes">
          <StudyNotesTab paperId={paperId} isReady={isReady} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
