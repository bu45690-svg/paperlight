import * as React from "react";
import { Link } from "react-router-dom";
import { FileText, MessageSquare, Layers, Star, Upload, ArrowRight } from "lucide-react";
import { PageHeader } from "@/components/layout/AppLayout";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { PaperCard } from "@/components/paper/PaperCard";
import { dashboardApi, papersApi } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import type { DashboardStats } from "@/types";

function StatCard({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: number | string }) {
  return (
    <Card>
      <CardContent className="p-5 flex items-center gap-4">
        <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="font-display text-2xl font-semibold leading-none">{value}</p>
          <p className="text-xs text-[var(--color-ink-soft)] mt-1">{label}</p>
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = React.useState<DashboardStats | null>(null);
  const [loading, setLoading] = React.useState(true);
  const { push } = useToast();

  const load = React.useCallback(async () => {
    try {
      const data = await dashboardApi.get();
      setStats(data);
    } catch {
      push({ kind: "error", title: "Couldn't load dashboard", description: "Check that the backend is running." });
    } finally {
      setLoading(false);
    }
  }, [push]);

  React.useEffect(() => {
    load();
  }, [load]);

  const handleToggleFavorite = async (id: string, next: boolean) => {
    await papersApi.toggleFavorite(id, next);
    load();
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-9 w-64" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  const hasNoPapers = (stats?.total_papers ?? 0) === 0;

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="An overview of your papers, reading activity, and AI conversations."
        actions={
          <Link to="/upload">
            <Button>
              <Upload className="h-4 w-4" /> Upload paper
            </Button>
          </Link>
        }
      />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard icon={FileText} label="Papers uploaded" value={stats?.total_papers ?? 0} />
        <StatCard icon={Layers} label="Total pages" value={stats?.total_pages ?? 0} />
        <StatCard icon={MessageSquare} label="Chat messages" value={stats?.total_chat_messages ?? 0} />
        <StatCard icon={Star} label="Favorites" value={stats?.favorite_papers.length ?? 0} />
      </div>

      {hasNoPapers ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--color-primary-soft)] text-[var(--color-primary)] mb-4">
              <FileText className="h-7 w-7" />
            </div>
            <h3 className="font-display text-lg font-semibold">No papers yet</h3>
            <p className="text-sm text-[var(--color-ink-soft)] mt-1 max-w-sm">
              Upload a research paper to get an instant AI analysis, chat with it using grounded citations, and
              generate study materials.
            </p>
            <Link to="/upload" className="mt-5">
              <Button>
                <Upload className="h-4 w-4" /> Upload your first paper
              </Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-8">
          {stats && stats.favorite_papers.length > 0 && (
            <section>
              <div className="flex items-center justify-between mb-3">
                <h2 className="font-display text-lg font-semibold flex items-center gap-2">
                  <Star className="h-4 w-4 text-[var(--color-warning)]" /> Favorite papers
                </h2>
              </div>
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {stats.favorite_papers.map((p) => (
                  <PaperCard key={p.id} paper={p} onToggleFavorite={handleToggleFavorite} />
                ))}
              </div>
            </section>
          )}

          <section>
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-display text-lg font-semibold">Recent uploads</h2>
              <Link to="/search" className="text-sm text-[var(--color-primary)] flex items-center gap-1 hover:underline">
                View all <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {stats?.recent_uploads.map((p) => (
                <PaperCard key={p.id} paper={p} onToggleFavorite={handleToggleFavorite} />
              ))}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
