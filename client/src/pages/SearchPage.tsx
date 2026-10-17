import * as React from "react";
import { Link } from "react-router-dom";
import { Search as SearchIcon, FileText } from "lucide-react";
import { PageHeader } from "@/components/layout/AppLayout";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { searchApi } from "@/lib/api";
import type { SearchResultItem } from "@/types";

export default function SearchPage() {
  const [query, setQuery] = React.useState("");
  const [results, setResults] = React.useState<SearchResultItem[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [searched, setSearched] = React.useState(false);
  const debounceRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  const runSearch = React.useCallback((q: string) => {
    if (!q.trim()) {
      setResults([]);
      setSearched(false);
      return;
    }
    setLoading(true);
    searchApi
      .searchAll(q)
      .then((res) => {
        setResults(res.results);
        setSearched(true);
      })
      .finally(() => setLoading(false));
  }, []);

  React.useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => runSearch(query), 450);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, runSearch]);

  return (
    <div>
      <PageHeader title="Search" description="Semantic search across every paper you've uploaded." />

      <div className="relative mb-6">
        <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--color-ink-soft)]" />
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search across all your papers…"
          className="pl-10 h-12 text-base"
          autoFocus
        />
      </div>

      {loading && (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      )}

      {!loading && searched && results.length === 0 && (
        <p className="text-sm text-[var(--color-ink-soft)] text-center py-10">No matching passages found.</p>
      )}

      {!loading && (
        <div className="space-y-3">
          {results.map((r, i) => (
            <Link key={i} to={`/papers/${r.paper_id}`}>
              <Card className="p-4 hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <FileText className="h-4 w-4 text-[var(--color-primary)] shrink-0" />
                    <span className="text-sm font-medium truncate">{r.paper_title || "Untitled paper"}</span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {r.page_number && <Badge variant="citation">Page {r.page_number}</Badge>}
                    <Badge variant="outline">{Math.round(r.score * 100)}% match</Badge>
                  </div>
                </div>
                <p className="text-sm text-[var(--color-ink-soft)] leading-relaxed">{r.snippet}</p>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
