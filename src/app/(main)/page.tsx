"use client";

import { Container } from "@/components/layout/container";
import { SearchBar } from "@/components/search/search-bar";
import { FilterPanel } from "@/components/search/filter-panel";
import { BillList } from "@/components/bills/bill-list";
import { Pagination } from "@/components/shared/pagination";
import { useBills, useSemanticSearch } from "@/hooks/use-bills";
import { useFilterStore } from "@/stores/filter-store";
import { Landmark } from "lucide-react";

export default function HomePage() {
  const filters = useFilterStore();
  const isSemanticMode = filters.searchMode === "semantic" && filters.q.length >= 3;

  const billsQuery = useBills({
    q: !isSemanticMode ? filters.q : undefined,
    status: filters.status || undefined,
    congress: filters.congress ? Number(filters.congress) : undefined,
    billType: filters.billType || undefined,
    dateFrom: filters.dateFrom || undefined,
    dateTo: filters.dateTo || undefined,
    page: filters.page,
    pageSize: filters.pageSize,
    sortBy: filters.sortBy,
    sortOrder: filters.sortOrder,
  });

  const semanticQuery = useSemanticSearch(
    isSemanticMode ? filters.q : "",
    filters.page,
    filters.pageSize
  );

  const activeQuery = isSemanticMode ? semanticQuery : billsQuery;
  const bills = activeQuery.data?.bills ?? [];
  const total = activeQuery.data?.total ?? 0;

  return (
    <Container className="py-6">
      {/* Hero */}
      <div className="mb-8 space-y-2">
        <div className="flex items-center gap-2">
          <Landmark className="size-6 text-primary" />
          <h1 className="text-2xl font-bold tracking-tight">
            Federal Bills Explainer
          </h1>
        </div>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Browse federal legislation with AI-powered plain-language explanations.
          Search by keyword or use AI search to find bills by meaning.
        </p>
      </div>

      {/* Search */}
      <div className="mb-6">
        <SearchBar />
      </div>

      {/* Content */}
      <div className="flex flex-col gap-6 lg:flex-row">
        {/* Sidebar filters — desktop */}
        <aside className="hidden w-64 shrink-0 lg:block">
          <div className="sticky top-20">
            <FilterPanel />
          </div>
        </aside>

        {/* Bill list */}
        <div className="min-w-0 flex-1">
          {isSemanticMode && filters.q && (
            <p className="mb-3 text-xs text-muted-foreground">
              AI search results for &ldquo;{filters.q}&rdquo;
            </p>
          )}

          <BillList
            bills={bills}
            isLoading={activeQuery.isLoading}
            emptyMessage={
              filters.q
                ? "No bills match your search. Try different keywords or switch search mode."
                : "No bills found with the current filters."
            }
          />

          <Pagination
            page={filters.page}
            pageSize={filters.pageSize}
            total={total}
            onPageChange={filters.setPage}
          />
        </div>
      </div>
    </Container>
  );
}
