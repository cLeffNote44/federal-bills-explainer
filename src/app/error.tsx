"use client";

import { AlertTriangle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-4">
      <AlertTriangle className="size-12 text-destructive/60" />
      <h1 className="text-lg font-bold">Something went wrong</h1>
      <p className="max-w-md text-center text-sm text-muted-foreground">
        {error.message || "An unexpected error occurred. Please try again."}
      </p>
      <Button onClick={reset} variant="outline" size="sm" className="gap-1.5">
        <RotateCcw className="size-3.5" />
        Try again
      </Button>
    </div>
  );
}
