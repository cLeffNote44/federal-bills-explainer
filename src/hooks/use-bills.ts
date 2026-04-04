"use client";

import { useQuery } from "@tanstack/react-query";
import type { Bill, BillWithExplanation, BillListResponse } from "@/types";

interface BillFilters {
  q?: string;
  status?: string;
  congress?: number;
  billType?: string;
  dateFrom?: string;
  dateTo?: string;
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: string;
}

async function fetchBills(filters: BillFilters): Promise<BillListResponse> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      params.set(key, String(value));
    }
  });
  const res = await fetch(`/api/bills?${params}`);
  if (!res.ok) throw new Error("Failed to fetch bills");
  return res.json();
}

async function fetchBillDetail(
  congress: number,
  billType: string,
  number: number
): Promise<BillWithExplanation> {
  const res = await fetch(`/api/bills/${congress}/${billType}/${number}`);
  if (!res.ok) throw new Error("Failed to fetch bill");
  return res.json();
}

async function searchBills(
  q: string,
  page = 1,
  pageSize = 20
): Promise<BillListResponse & { bills: (Bill & { similarity: number })[] }> {
  const params = new URLSearchParams({ q, page: String(page), pageSize: String(pageSize) });
  const res = await fetch(`/api/search?${params}`);
  if (!res.ok) throw new Error("Failed to search bills");
  return res.json();
}

export function useBills(filters: BillFilters) {
  return useQuery({
    queryKey: ["bills", filters],
    queryFn: () => fetchBills(filters),
  });
}

export function useBillDetail(
  congress: number,
  billType: string,
  number: number
) {
  return useQuery({
    queryKey: ["bill", congress, billType, number],
    queryFn: () => fetchBillDetail(congress, billType, number),
  });
}

export function useSemanticSearch(q: string, page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ["search", q, page, pageSize],
    queryFn: () => searchBills(q, page, pageSize),
    enabled: q.length >= 3,
  });
}
