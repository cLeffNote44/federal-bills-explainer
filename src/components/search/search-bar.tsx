"use client";

import { useState, useCallback } from "react";
import { Search, Sparkles, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useFilterStore } from "@/stores/filter-store";
import { cn } from "@/lib/utils";

export function SearchBar() {
  const { q, searchMode, setQ, setSearchMode } = useFilterStore();
  const [localValue, setLocalValue] = useState(q);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      setQ(localValue);
    },
    [localValue, setQ]
  );

  const handleClear = useCallback(() => {
    setLocalValue("");
    setQ("");
  }, [setQ]);

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2">
      <div className="relative flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={localValue}
            onChange={(e) => setLocalValue(e.target.value)}
            placeholder={
              searchMode === "semantic"
                ? "Describe what you're looking for..."
                : "Search bills by keyword..."
            }
            className="pl-9 pr-8"
          />
          {localValue && (
            <button
              type="button"
              onClick={handleClear}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <X className="size-3.5" />
            </button>
          )}
        </div>
        <Button type="submit" size="default">
          Search
        </Button>
      </div>

      {/* Search mode toggle */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setSearchMode("text")}
          className={cn(
            "flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium transition-colors",
            searchMode === "text"
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <Search className="size-3" />
          Keyword
        </button>
        <button
          type="button"
          onClick={() => setSearchMode("semantic")}
          className={cn(
            "flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium transition-colors",
            searchMode === "semantic"
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <Sparkles className="size-3" />
          AI Search
        </button>
      </div>
    </form>
  );
}
