import { create } from "zustand";

interface FilterState {
  q: string;
  status: string;
  congress: string;
  billType: string;
  dateFrom: string;
  dateTo: string;
  page: number;
  pageSize: number;
  sortBy: string;
  sortOrder: string;
  searchMode: "text" | "semantic";

  setQ: (q: string) => void;
  setStatus: (status: string) => void;
  setCongress: (congress: string) => void;
  setBillType: (billType: string) => void;
  setDateFrom: (dateFrom: string) => void;
  setDateTo: (dateTo: string) => void;
  setPage: (page: number) => void;
  setSortBy: (sortBy: string) => void;
  setSortOrder: (sortOrder: string) => void;
  setSearchMode: (mode: "text" | "semantic") => void;
  resetFilters: () => void;
}

const defaults = {
  q: "",
  status: "",
  congress: "",
  billType: "",
  dateFrom: "",
  dateTo: "",
  page: 1,
  pageSize: 20,
  sortBy: "date",
  sortOrder: "desc",
  searchMode: "text" as const,
};

export const useFilterStore = create<FilterState>((set) => ({
  ...defaults,
  setQ: (q) => set({ q, page: 1 }),
  setStatus: (status) => set({ status, page: 1 }),
  setCongress: (congress) => set({ congress, page: 1 }),
  setBillType: (billType) => set({ billType, page: 1 }),
  setDateFrom: (dateFrom) => set({ dateFrom, page: 1 }),
  setDateTo: (dateTo) => set({ dateTo, page: 1 }),
  setPage: (page) => set({ page }),
  setSortBy: (sortBy) => set({ sortBy }),
  setSortOrder: (sortOrder) => set({ sortOrder }),
  setSearchMode: (searchMode) => set({ searchMode }),
  resetFilters: () => set(defaults),
}));
