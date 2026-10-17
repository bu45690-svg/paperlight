import { Badge } from "@/components/ui/Badge";
import type { PaperStatus } from "@/types";
import { Loader2, CheckCircle2, XCircle, Clock } from "lucide-react";

const STATUS_META: Record<PaperStatus, { label: string; variant: "default" | "primary" | "success" | "danger" }> = {
  uploaded: { label: "Queued", variant: "default" },
  extracting: { label: "Extracting text", variant: "primary" },
  indexing: { label: "Indexing", variant: "primary" },
  analyzing: { label: "Analyzing with AI", variant: "primary" },
  ready: { label: "Ready", variant: "success" },
  failed: { label: "Failed", variant: "danger" },
};

export function StatusBadge({ status }: { status: PaperStatus }) {
  const meta = STATUS_META[status];
  const isProcessing = !["ready", "failed", "uploaded"].includes(status);
  return (
    <Badge variant={meta.variant}>
      {isProcessing && <Loader2 className="h-3 w-3 animate-spin" />}
      {status === "ready" && <CheckCircle2 className="h-3 w-3" />}
      {status === "failed" && <XCircle className="h-3 w-3" />}
      {status === "uploaded" && <Clock className="h-3 w-3" />}
      {meta.label}
    </Badge>
  );
}
