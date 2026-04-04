"use client";

import { useState } from "react";
import { Download, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ExportButtonProps {
  congress: number;
  billType: string;
  number: number;
}

export function ExportButton({ congress, billType, number }: ExportButtonProps) {
  const [loading, setLoading] = useState(false);

  async function handleExport() {
    setLoading(true);
    try {
      const res = await fetch(
        `/api/export?format=json&includeExplanations=true&congress=${congress}`
      );
      if (!res.ok) throw new Error("Export failed");

      const data = await res.json();

      // Find the specific bill
      const bill = data.bills?.find(
        (b: { congress: number; billType: string; number: number }) =>
          b.congress === congress && b.billType === billType && b.number === number
      );

      const exportData = bill ?? data;

      // Download as JSON file
      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${billType.toUpperCase()}-${number}-${congress}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Export failed:", error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleExport}
      disabled={loading}
      className="gap-1.5"
    >
      {loading ? (
        <Loader2 className="size-3.5 animate-spin" />
      ) : (
        <Download className="size-3.5" />
      )}
      Export
    </Button>
  );
}
