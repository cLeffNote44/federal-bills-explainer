"use client";

import { useQuery } from "@tanstack/react-query";
import { ThumbsUp, ThumbsDown } from "lucide-react";
import type { FeedbackStats } from "@/types";

interface FeedbackStatsDisplayProps {
  explanationId: string;
}

export function FeedbackStatsDisplay({ explanationId }: FeedbackStatsDisplayProps) {
  const { data } = useQuery<FeedbackStats>({
    queryKey: ["feedback-stats", explanationId],
    queryFn: async () => {
      const res = await fetch(`/api/feedback?explanationId=${explanationId}`);
      if (!res.ok) throw new Error("Failed to fetch feedback stats");
      return res.json();
    },
    enabled: !!explanationId,
  });

  if (!data || data.total === 0) return null;

  return (
    <div className="flex items-center gap-3 text-xs text-muted-foreground">
      <span className="flex items-center gap-1">
        <ThumbsUp className="size-3" />
        {data.helpful}
      </span>
      <span className="flex items-center gap-1">
        <ThumbsDown className="size-3" />
        {data.notHelpful}
      </span>
      <span>{data.helpfulPercentage}% found helpful</span>
    </div>
  );
}
