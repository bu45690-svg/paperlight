import * as React from "react";
import { useNavigate } from "react-router-dom";
import { UploadCloud, FileText, X, Loader2, CheckCircle2, XCircle } from "lucide-react";
import { PageHeader } from "@/components/layout/AppLayout";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Progress } from "@/components/ui/Progress";
import { papersApi, getApiErrorMessage } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import { formatBytes, cn } from "@/lib/utils";

interface QueuedFile {
  id: string;
  file: File;
  progress: number;
  state: "pending" | "uploading" | "done" | "error";
  error?: string;
  paperId?: string;
}

export default function UploadPage() {
  const [queue, setQueue] = React.useState<QueuedFile[]>([]);
  const [isDragging, setIsDragging] = React.useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const { push } = useToast();
  const navigate = useNavigate();

  const addFiles = (files: FileList | File[]) => {
    const pdfFiles = Array.from(files).filter((f) => f.type === "application/pdf" || f.name.toLowerCase().endsWith(".pdf"));
    const rejected = Array.from(files).length - pdfFiles.length;
    if (rejected > 0) {
      push({ kind: "error", title: "Only PDF files are supported", description: `${rejected} file(s) were skipped.` });
    }
    const newItems: QueuedFile[] = pdfFiles.map((file) => ({
      id: crypto.randomUUID(),
      file,
      progress: 0,
      state: "pending",
    }));
    setQueue((prev) => [...prev, ...newItems]);
    newItems.forEach(uploadOne);
  };

  const uploadOne = async (item: QueuedFile) => {
    setQueue((prev) => prev.map((q) => (q.id === item.id ? { ...q, state: "uploading" } : q)));
    try {
      const result = await papersApi.upload(item.file, (pct) => {
        setQueue((prev) => prev.map((q) => (q.id === item.id ? { ...q, progress: pct } : q)));
      });
      setQueue((prev) =>
        prev.map((q) => (q.id === item.id ? { ...q, state: "done", progress: 100, paperId: result.id } : q))
      );
    } catch (err) {
      setQueue((prev) =>
        prev.map((q) => (q.id === item.id ? { ...q, state: "error", error: getApiErrorMessage(err) } : q))
      );
    }
  };

  const removeItem = (id: string) => setQueue((prev) => prev.filter((q) => q.id !== id));

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files.length) addFiles(e.dataTransfer.files);
  };

  const onFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) addFiles(e.target.files);
    e.target.value = "";
  };

  const doneCount = queue.filter((q) => q.state === "done").length;

  return (
    <div>
      <PageHeader
        title="Upload research papers"
        description="Drop one or more PDFs to get instant AI analysis, RAG-grounded chat, and study materials."
      />

      <Card
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        className={cn(
          "border-2 border-dashed p-10 text-center transition-colors",
          isDragging ? "border-[var(--color-primary)] bg-[var(--color-primary-soft)]" : "border-[var(--color-border)]"
        )}
      >
        <div className="flex flex-col items-center">
          <div
            className={cn(
              "flex h-16 w-16 items-center justify-center rounded-2xl bg-[var(--color-primary-soft)] text-[var(--color-primary)] mb-4",
              isDragging && "animate-pulse-ring"
            )}
          >
            <UploadCloud className="h-8 w-8" />
          </div>
          <h3 className="font-display text-lg font-semibold">Drag and drop PDFs here</h3>
          <p className="text-sm text-[var(--color-ink-soft)] mt-1">or click below to browse — up to 25MB per file</p>
          <input ref={fileInputRef} type="file" accept=".pdf,application/pdf" multiple className="hidden" onChange={onFileInput} />
          <Button className="mt-5" onClick={() => fileInputRef.current?.click()}>
            Browse files
          </Button>
        </div>
      </Card>

      {queue.length > 0 && (
        <div className="mt-6 space-y-3">
          {queue.map((item) => (
            <Card key={item.id} className="p-4 flex items-center gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--color-surface-2)]">
                <FileText className="h-5 w-5 text-[var(--color-ink-soft)]" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium truncate">{item.file.name}</p>
                  <span className="text-xs text-[var(--color-ink-soft)] shrink-0">{formatBytes(item.file.size)}</span>
                </div>
                {item.state === "uploading" && <Progress value={item.progress} className="h-1.5 mt-2" />}
                {item.state === "error" && <p className="text-xs text-[var(--color-danger)] mt-1">{item.error}</p>}
                {item.state === "done" && <p className="text-xs text-[var(--color-success)] mt-1">Uploaded — processing in background</p>}
              </div>
              <div className="shrink-0">
                {item.state === "uploading" && <Loader2 className="h-4 w-4 animate-spin text-[var(--color-primary)]" />}
                {item.state === "done" && <CheckCircle2 className="h-4 w-4 text-[var(--color-success)]" />}
                {item.state === "error" && <XCircle className="h-4 w-4 text-[var(--color-danger)]" />}
                {item.state === "pending" && (
                  <button onClick={() => removeItem(item.id)} aria-label="Remove">
                    <X className="h-4 w-4 text-[var(--color-ink-soft)]" />
                  </button>
                )}
              </div>
            </Card>
          ))}

          {doneCount > 0 && (
            <div className="flex justify-end pt-2">
              <Button variant="secondary" onClick={() => navigate("/")}>
                Go to dashboard
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
