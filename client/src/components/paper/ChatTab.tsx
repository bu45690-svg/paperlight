import * as React from "react";
import { Send, Copy, Check, FileDown } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/Button";
import { Textarea } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { chatApi, getApiErrorMessage } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import { confidenceLabel } from "@/lib/utils";
import type { ChatAnswer } from "@/types";

const SUGGESTED_QUESTIONS = [
  "What is the main contribution?",
  "Explain the methodology.",
  "What datasets were used?",
  "What are the limitations?",
];

function ConfidenceMeter({ score }: { score: number }) {
  const { label, tone } = confidenceLabel(score);
  const toneColor =
    tone === "high" ? "bg-[var(--color-success)]" : tone === "medium" ? "bg-[var(--color-warning)]" : "bg-[var(--color-danger)]";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 rounded-full bg-[var(--color-surface-2)] overflow-hidden">
        <div className={`h-full ${toneColor}`} style={{ width: `${Math.round(score * 100)}%` }} />
      </div>
      <span className="text-xs text-[var(--color-ink-soft)] font-mono-tag">{Math.round(score * 100)}% · {label}</span>
    </div>
  );
}

function AnswerBubble({ message }: { message: ChatAnswer }) {
  const [copied, setCopied] = React.useState(false);

  const copyAnswer = async () => {
    await navigator.clipboard.writeText(message.answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="animate-fade-in-up space-y-3">
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-[var(--color-primary)] text-white px-4 py-2.5 text-sm">
          {message.question}
        </div>
      </div>

      <div className="flex gap-3">
        <div className="flex-1 min-w-0">
          <Card className="p-4 rounded-tl-sm">
            <div className="prose prose-sm max-w-none dark:prose-invert prose-p:leading-relaxed">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.answer}</ReactMarkdown>
            </div>

            <div className="flex items-center justify-between mt-3 pt-3 border-t border-[var(--color-border)]">
              <ConfidenceMeter score={message.confidence_score} />
              <button onClick={copyAnswer} className="flex items-center gap-1 text-xs text-[var(--color-ink-soft)] hover:text-[var(--color-ink)]">
                {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
          </Card>

          {(message.page_numbers?.length || message.citations?.length) ? (
            <div className="mt-2 flex flex-wrap gap-2">
              {message.page_numbers?.map((page, i) => (
                <div key={`p-${i}`} className="margin-note bg-[var(--color-citation-soft)] px-3 py-2 max-w-xs">
                  <div className="flex items-center gap-1.5 mb-1">
                    <Badge variant="citation">Page {page}</Badge>
                  </div>
                  {message.citations?.[i] && (
                    <p className="text-xs text-[var(--color-ink-soft)] italic leading-snug">"{message.citations[i]}"</p>
                  )}
                </div>
              ))}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export function ChatTab({ paperId, isReady }: { paperId: string; isReady: boolean }) {
  const [messages, setMessages] = React.useState<ChatAnswer[]>([]);
  const [question, setQuestion] = React.useState("");
  const [asking, setAsking] = React.useState(false);
  const [loadingHistory, setLoadingHistory] = React.useState(true);
  const { push } = useToast();
  const scrollRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    chatApi
      .history(paperId)
      .then(setMessages)
      .catch(() => push({ kind: "error", title: "Couldn't load chat history" }))
      .finally(() => setLoadingHistory(false));
  }, [paperId, push]);

  React.useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const ask = async (q: string) => {
    if (!q.trim() || asking) return;
    setAsking(true);
    setQuestion("");
    try {
      const answer = await chatApi.ask(paperId, q);
      setMessages((prev) => [...prev, answer]);
    } catch (err) {
      push({ kind: "error", title: "Couldn't get an answer", description: getApiErrorMessage(err) });
    } finally {
      setAsking(false);
    }
  };

  const downloadChat = () => {
    const text = messages
      .map((m) => `Q: ${m.question}\nA: ${m.answer}\nPages: ${(m.page_numbers || []).join(", ")}\nConfidence: ${Math.round(m.confidence_score * 100)}%\n`)
      .join("\n---\n\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "chat-history.txt";
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!isReady) {
    return (
      <Card className="p-8 text-center text-sm text-[var(--color-ink-soft)]">
        This paper is still processing. Chat will be available once analysis is complete.
      </Card>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-280px)] min-h-[400px]">
      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-6 pr-1">
        {loadingHistory ? (
          <p className="text-sm text-[var(--color-ink-soft)]">Loading conversation…</p>
        ) : messages.length === 0 ? (
          <div className="text-center py-10">
            <p className="text-sm text-[var(--color-ink-soft)] mb-4">
              Ask anything about this paper — answers are grounded only in its content, with page citations.
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {SUGGESTED_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => ask(q)}
                  className="rounded-full border border-[var(--color-border)] px-3 py-1.5 text-xs hover:bg-[var(--color-surface-2)]"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m) => <AnswerBubble key={m.id} message={m} />)
        )}
        {asking && <p className="text-xs text-[var(--color-ink-soft)] animate-pulse">Reading the paper and composing an answer…</p>}
      </div>

      <div className="border-t border-[var(--color-border)] pt-4 mt-4">
        {messages.length > 0 && (
          <div className="flex justify-end mb-2">
            <button onClick={downloadChat} className="flex items-center gap-1 text-xs text-[var(--color-ink-soft)] hover:text-[var(--color-ink)]">
              <FileDown className="h-3.5 w-3.5" /> Download chat
            </button>
          </div>
        )}
        <div className="flex gap-2">
          <Textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                ask(question);
              }
            }}
            placeholder="Ask a question about this paper…"
            className="min-h-11 max-h-32 resize-none"
            rows={1}
          />
          <Button onClick={() => ask(question)} loading={asking} disabled={!question.trim()} size="icon">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
