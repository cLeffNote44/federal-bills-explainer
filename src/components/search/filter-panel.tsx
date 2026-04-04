"use client";

import { useFilterStore } from "@/stores/filter-store";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { RotateCcw } from "lucide-react";
import { BILL_STATUSES, BILL_TYPES } from "@/lib/validators";

export function FilterPanel() {
  const {
    status,
    congress,
    billType,
    dateFrom,
    dateTo,
    sortBy,
    sortOrder,
    setStatus,
    setCongress,
    setBillType,
    setDateFrom,
    setDateTo,
    setSortBy,
    setSortOrder,
    resetFilters,
  } = useFilterStore();

  const hasFilters = status || congress || billType || dateFrom || dateTo;

  return (
    <div className="space-y-4 rounded-lg border border-border bg-card p-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">Filters</h3>
        {hasFilters && (
          <Button
            variant="ghost"
            size="xs"
            onClick={resetFilters}
            className="gap-1 text-muted-foreground"
          >
            <RotateCcw className="size-3" />
            Reset
          </Button>
        )}
      </div>

      {/* Status */}
      <div className="space-y-1.5">
        <Label className="text-xs text-muted-foreground">Status</Label>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="w-full rounded-md border border-input bg-background px-2.5 py-1.5 text-sm"
        >
          <option value="">All statuses</option>
          {BILL_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
            </option>
          ))}
        </select>
      </div>

      {/* Congress */}
      <div className="space-y-1.5">
        <Label className="text-xs text-muted-foreground">Congress</Label>
        <select
          value={congress}
          onChange={(e) => setCongress(e.target.value)}
          className="w-full rounded-md border border-input bg-background px-2.5 py-1.5 text-sm"
        >
          <option value="">All</option>
          <option value="119">119th (2025-2027)</option>
          <option value="118">118th (2023-2025)</option>
          <option value="117">117th (2021-2023)</option>
          <option value="116">116th (2019-2021)</option>
        </select>
      </div>

      {/* Bill Type */}
      <div className="space-y-1.5">
        <Label className="text-xs text-muted-foreground">Bill Type</Label>
        <select
          value={billType}
          onChange={(e) => setBillType(e.target.value)}
          className="w-full rounded-md border border-input bg-background px-2.5 py-1.5 text-sm"
        >
          <option value="">All types</option>
          {BILL_TYPES.map((t) => (
            <option key={t} value={t}>
              {t.toUpperCase()}
            </option>
          ))}
        </select>
      </div>

      {/* Date Range */}
      <div className="grid grid-cols-2 gap-2">
        <div className="space-y-1.5">
          <Label className="text-xs text-muted-foreground">From</Label>
          <Input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="text-xs"
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs text-muted-foreground">To</Label>
          <Input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="text-xs"
          />
        </div>
      </div>

      {/* Sort */}
      <div className="grid grid-cols-2 gap-2">
        <div className="space-y-1.5">
          <Label className="text-xs text-muted-foreground">Sort by</Label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-2.5 py-1.5 text-sm"
          >
            <option value="date">Date</option>
            <option value="congress">Congress</option>
            <option value="number">Number</option>
          </select>
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs text-muted-foreground">Order</Label>
          <select
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-2.5 py-1.5 text-sm"
          >
            <option value="desc">Newest first</option>
            <option value="asc">Oldest first</option>
          </select>
        </div>
      </div>
    </div>
  );
}
