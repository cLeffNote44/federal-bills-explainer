"use client";

import { useState } from "react";
import { Brain, Lightbulb, ThumbsUp, ThumbsDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { Explanation } from "@/types";

interface BillExplanationProps {
  explanation: Explanation;
}

export function BillExplanation({ explanation }: BillExplanationProps) {
  const [mode, setMode] = useState<"full" | "simple">("full");
  const [feedbackGiven, setFeedbackGiven] = useState<boolean | null>(null);

  const text = mode === "simple" && explanation.simpleText
    ? explanation.simpleText
    : explanation.text;

  async function submitFeedback(isHelpful: boolean) {
    setFeedbackGiven(isHelpful);
    try {
      await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          explanationId: explanation.id,
          isHelpful,
        }),
      });
    } catch {
      // Best-effort
    }
  }

  return (
    <div className="space-y-4 rounded-lg border border-border bg-card p-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <Brain className="size-4 text-primary" />
          <h2 className="text-sm font-semibold">AI Explanation</h2>
          <Badge variant="secondary" className="text-[10px]">
            {explanation.modelProvider}
          </Badge>
        </div>

        {/* ELI5 toggle */}
        {explanation.simpleText && (
          <div className="flex rounded-md border border-border bg-muted/50 p-0.5">
            <button
              onClick={() => setMode("full")}
              className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                mode === "full"
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Full
            </button>
            <button
              onClick={() => setMode("simple")}
              className={`flex items-center gap-1 rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                mode === "simple"
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Lightbulb className="size-3" />
              ELI5
            </button>
          </div>
        )}
      </div>

      {/* Explanation text */}
      <div className="prose prose-sm dark:prose-invert max-w-none">
        {text.split("\n").map((paragraph, i) => (
          <p key={i}>{paragraph}</p>
        ))}
      </div>

      {/* Feedback */}
      <div className="flex items-center gap-2 border-t border-border pt-3">
        <span className="text-xs text-muted-foreground">Was this helpful?</span>
        {feedbackGiven === null ? (
          <>
            <Button
              variant="ghost"
              size="icon-xs"
              onClick={() => submitFeedback(true)}
              aria-label="Helpful"
            >
              <ThumbsUp className="size-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="icon-xs"
              onClick={() => submitFeedback(false)}
              aria-label="Not helpful"
            >
              <ThumbsDown className="size-3.5" />
            </Button>
          </>
        ) : (
          <span className="text-xs text-muted-foreground">
            Thanks for the feedback!
          </span>
        )}
      </div>
    </div>
  );
}
