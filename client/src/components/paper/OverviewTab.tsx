import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import type { PaperAnalysis } from "@/types";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

function ProseText({ text }: { text: string | null }) {
  if (!text) return <p className="text-sm text-[var(--color-ink-soft)] italic">Not available.</p>;
  return <p className="text-sm leading-relaxed whitespace-pre-line">{text}</p>;
}

function BulletBlock({ items }: { items: string[] | null }) {
  if (!items || items.length === 0) return <p className="text-sm text-[var(--color-ink-soft)] italic">None identified.</p>;
  return (
    <ul className="space-y-2">
      {items.map((item, i) => (
        <li key={i} className="flex gap-2 text-sm">
          <span className="text-[var(--color-primary)] mt-1">•</span>
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

export function OverviewTab({ paper, loading }: { paper: PaperAnalysis | null; loading: boolean }) {
  if (loading || !paper) {
    return (
      <div className="grid md:grid-cols-2 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-40" />
        ))}
      </div>
    );
  }

  if (paper.status === "failed") {
    return (
      <Card className="p-6">
        <p className="text-sm text-[var(--color-danger)] font-medium">Processing failed</p>
        <p className="text-sm text-[var(--color-ink-soft)] mt-1">{paper.error_message}</p>
      </Card>
    );
  }

  if (paper.status !== "ready") {
    return (
      <Card className="p-8 text-center">
        <p className="text-sm text-[var(--color-ink-soft)]">
          Your paper is being processed — this page will update automatically once analysis is complete.
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid md:grid-cols-3 gap-4">
        <Card className="p-4">
          <p className="text-xs text-[var(--color-ink-soft)]">Total pages</p>
          <p className="font-display text-2xl font-semibold">{paper.total_pages}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-[var(--color-ink-soft)]">References</p>
          <p className="font-display text-2xl font-semibold">{paper.references_count}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-[var(--color-ink-soft)]">Key contributions</p>
          <p className="font-display text-2xl font-semibold">{paper.key_contributions?.length ?? 0}</p>
        </Card>
      </div>

      <Section title="Executive Summary">
        <ProseText text={paper.executive_summary} />
      </Section>

      <Section title="Abstract Summary">
        <ProseText text={paper.abstract_summary} />
      </Section>

      <div className="grid md:grid-cols-2 gap-4">
        <Section title="Key Contributions">
          <BulletBlock items={paper.key_contributions} />
        </Section>
        <Section title="Methodology">
          <ProseText text={paper.methodology} />
        </Section>
        <Section title="Results">
          <ProseText text={paper.results} />
        </Section>
        <Section title="Limitations">
          <ProseText text={paper.limitations} />
        </Section>
        <Section title="Future Work">
          <ProseText text={paper.future_work} />
        </Section>
        <Section title="Important Equations">
          <BulletBlock items={paper.important_equations} />
        </Section>
        <Section title="Important Figures">
          <BulletBlock items={paper.important_figures} />
        </Section>
        <Section title="Keywords">
          {paper.keywords && paper.keywords.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {paper.keywords.map((k) => (
                <Badge key={k} variant="primary">{k}</Badge>
              ))}
            </div>
          ) : (
            <p className="text-sm text-[var(--color-ink-soft)] italic">None identified.</p>
          )}
        </Section>
      </div>
    </div>
  );
}
