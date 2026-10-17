import * as React from "react";
import { papersApi } from "@/lib/api";
import type { PaperStatus } from "@/types";

export function usePaperStatusPolling(paperId: string | undefined, currentStatus: PaperStatus | undefined, onSettled?: () => void) {
  const [status, setStatus] = React.useState<PaperStatus | undefined>(currentStatus);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);

  React.useEffect(() => {
    setStatus(currentStatus);
  }, [currentStatus]);

  React.useEffect(() => {
    if (!paperId || !status || status === "ready" || status === "failed") return;

    let cancelled = false;
    const interval = setInterval(async () => {
      try {
        const result = await papersApi.getStatus(paperId);
        if (cancelled) return;
        setStatus(result.status as PaperStatus);
        setErrorMessage(result.error_message);
        if (result.status === "ready" || result.status === "failed") {
          clearInterval(interval);
          onSettled?.();
        }
      } catch {
        // transient network error while polling — keep trying
      }
    }, 2500);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paperId, status]);

  return { status, errorMessage };
}
