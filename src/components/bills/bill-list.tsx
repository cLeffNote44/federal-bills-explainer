"use client";

import { BillCard } from "./bill-card";
import { Skeleton } from "@/components/ui/skeleton";
import { FileQuestion } from "lucide-react";
import type { Bill } from "@/types";

interface BillListProps {
  bills: Bill[];
  isLoading?: boolean;
  emptyMessage?: string;
}

export function BillList({
  bills,
  isLoading,
  emptyMessage = "No bills found.",
}: BillListProps) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-28 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (!bills.length) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-16 text-muted-foreground">
        <FileQuestion className="size-10 opacity-40" />
        <p className="text-sm">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {bills.map((bill) => (
        <BillCard key={bill.id} bill={bill} />
      ))}
    </div>
  );
}
