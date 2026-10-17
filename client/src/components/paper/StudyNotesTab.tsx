import * as React from "react";
import { Sparkles, ChevronLeft, ChevronRight, RotateCw, Download, CheckCircle2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/Tabs";
import { notesApi, exportApi, getApiErrorMessage } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import { cn } from "@/lib/utils";
import type { StudyNotes } from "@/types";

function FlashcardDeck({ cards }: { cards: StudyNotes["flashcards"] }) {
  const [index, setIndex] = React.useState(0);
  const [flipped, setFlipped] = React.useState(false);

  if (!cards || cards.length === 0) return <EmptyState label="No flashcards generated." />;

  const card = cards[index];
  const next = () => {
    setFlipped(false);
    setIndex((i) => (i + 1) % cards.length);
  };
  const prev = () => {
    setFlipped(false);
    setIndex((i) => (i - 1 + cards.length) % cards.length);
  };

  return (
    <div className="flex flex-col items-center">
      <p className="text-xs text-[var(--color-ink-soft)] mb-3">
        Card {index + 1} of {cards.length}
      </p>
      <button
        onClick={() => setFlipped((f) => !f)}
        className="w-full max-w-lg h-56 [perspective:1000px]"
        aria-label="Flip flashcard"
      >
        <div
          className="relative h-full w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm transition-transform duration-500 [transform-style:preserve-3d]"
          style={{ transform: flipped ? "rotateY(180deg)" : "rotateY(0deg)" }}
        >
          <div className="absolute inset-0 flex items-center justify-center p-6 [backface-visibility:hidden]">
            <div className="text-center">
              <Badge variant="primary" className="mb-3">Question</Badge>
              <p className="font-display text-lg">{card.question}</p>
            </div>
          </div>
          <div
            className="absolute inset-0 flex items-center justify-center p-6 [backface-visibility:hidden] bg-[var(--color-primary-soft)] rounded-xl"
            style={{ transform: "rotateY(180deg)" }}
          >
            <div className="text-center">
              <Badge variant="citation" className="mb-3">Answer</Badge>
              <p className="text-sm">{card.answer}</p>
            </div>
          </div>
        </div>
      </button>
      <div className="flex items-center gap-3 mt-4">
        <Button variant="outline" size="icon" onClick={prev}>
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={() => setFlipped((f) => !f)}>
          <RotateCw className="h-3.5 w-3.5" /> Flip
        </Button>
        <Button variant="outline" size="icon" onClick={next}>
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

function MCQList({ mcqs }: { mcqs: StudyNotes["mcqs"] }) {
  const [selected, setSelected] = React.useState<Record<number, number>>({});

  if (!mcqs || mcqs.length === 0) return <EmptyState label="No MCQs generated." />;

  return (
    <div className="space-y-5">
      {mcqs.map((mcq, qi) => {
        const chosen = selected[qi];
        return (
          <Card key={qi} className="p-4">
            <p className="text-sm font-medium mb-3">
              {qi + 1}. {mcq.question}
            </p>
            <div className="space-y-2">
              {mcq.options.map((opt, oi) => {
                const isChosen = chosen === oi;
                const isCorrect = oi === mcq.correct_answer_index;
                const showResult = chosen !== undefined;
                return (
                  <button
                    key={oi}
                    onClick={() => setSelected((s) => ({ ...s, [qi]: oi }))}
                    disabled={showResult}
                    className={cn(
                      "w-full flex items-center justify-between rounded-lg border px-3 py-2 text-left text-sm transition-colors",
                      showResult && isCorrect && "border-[var(--color-success)] bg-green-50 dark:bg-green-950/40",
                      showResult && isChosen && !isCorrect && "border-[var(--color-danger)] bg-red-50 dark:bg-red-950/40",
                      !showResult && "border-[var(--color-border)] hover:bg-[var(--color-surface-2)]"
                    )}
                  >
                    {opt}
                    {showResult && isCorrect && <CheckCircle2 className="h-4 w-4 text-[var(--color-success)]" />}
                    {showResult && isChosen && !isCorrect && <XCircle className="h-4 w-4 text-[var(--color-danger)]" />}
                  </button>
                );
              })}
            </div>
            {chosen !== undefined && mcq.explanation && (
              <p className="text-xs text-[var(--color-ink-soft)] mt-2">{mcq.explanation}</p>
            )}
          </Card>
        );
      })}
    </div>
  );
}

function BulletList({ items }: { items: string[] | null }) {
  if (!items || items.length === 0) return <EmptyState label="Nothing generated yet." />;
  return (
    <ul className="space-y-2.5">
      {items.map((item, i) => (
        <li key={i} className="flex gap-2 text-sm">
          <span className="text-[var(--color-primary)] mt-1">•</span>
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

function EmptyState({ label }: { label: string }) {
  return <p className="text-sm text-[var(--color-ink-soft)] text-center py-8">{label}</p>;
}

export function StudyNotesTab({ paperId, isReady }: { paperId: string; isReady: boolean }) {
  const [notes, setNotes] = React.useState<StudyNotes | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [generating, setGenerating] = React.useState(false);
  const { push } = useToast();

  React.useEffect(() => {
    notesApi
      .get(paperId)
      .then(setNotes)
      .finally(() => setLoading(false));
  }, [paperId]);

  const generate = async () => {
    setGenerating(true);
    try {
      const result = await notesApi.generate(paperId);
      setNotes(result);
      push({ kind: "success", title: "Study notes generated" });
    } catch (err) {
      push({ kind: "error", title: "Couldn't generate study notes", description: getApiErrorMessage(err) });
    } finally {
      setGenerating(false);
    }
  };

  if (!isReady) {
    return <Card className="p-8 text-center text-sm text-[var(--color-ink-soft)]">This paper is still processing.</Card>;
  }

  if (loading) return <p className="text-sm text-[var(--color-ink-soft)]">Loading study notes…</p>;

  if (!notes) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center py-14 text-center">
          <Sparkles className="h-8 w-8 text-[var(--color-primary)] mb-3" />
          <h3 className="font-display text-lg font-semibold">Generate study materials</h3>
          <p className="text-sm text-[var(--color-ink-soft)] mt-1 max-w-sm">
            Create exam notes, flashcards, MCQs, and interview/viva questions from this paper in one click.
          </p>
          <Button className="mt-5" onClick={generate} loading={generating}>
            <Sparkles className="h-4 w-4" /> Generate study notes
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div>
      <div className="flex justify-end gap-2 mb-4">
        <Button variant="outline" size="sm" onClick={generate} loading={generating}>
          <RotateCw className="h-3.5 w-3.5" /> Regenerate
        </Button>
        <a href={exportApi.downloadUrl(paperId, "study-notes")}>
          <Button variant="secondary" size="sm">
            <Download className="h-3.5 w-3.5" /> Export notes
          </Button>
        </a>
        <a href={exportApi.downloadUrl(paperId, "flashcards")}>
          <Button variant="secondary" size="sm">
            <Download className="h-3.5 w-3.5" /> Export flashcards
          </Button>
        </a>
      </div>

      <Tabs defaultValue="flashcards">
        <TabsList className="flex-wrap h-auto">
          <TabsTrigger value="flashcards">Flashcards</TabsTrigger>
          <TabsTrigger value="mcqs">MCQs</TabsTrigger>
          <TabsTrigger value="exam">Exam notes</TabsTrigger>
          <TabsTrigger value="bullets">Bullet notes</TabsTrigger>
          <TabsTrigger value="interview">Interview Qs</TabsTrigger>
          <TabsTrigger value="viva">Viva Qs</TabsTrigger>
        </TabsList>

        <TabsContent value="flashcards">
          <FlashcardDeck cards={notes.flashcards} />
        </TabsContent>
        <TabsContent value="mcqs">
          <MCQList mcqs={notes.mcqs} />
        </TabsContent>
        <TabsContent value="exam">
          <BulletList items={notes.exam_notes} />
        </TabsContent>
        <TabsContent value="bullets">
          <BulletList items={notes.bullet_notes} />
        </TabsContent>
        <TabsContent value="interview">
          <BulletList items={notes.interview_questions} />
        </TabsContent>
        <TabsContent value="viva">
          <BulletList items={notes.viva_questions} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
