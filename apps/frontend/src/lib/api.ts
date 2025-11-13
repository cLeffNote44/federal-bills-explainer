import ky from 'ky';

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export const api = ky.create({
  prefixUrl: apiBase,
  timeout: 30000,
  retry: {
    limit: 2,
    methods: ['get'],
    statusCodes: [408, 429, 500, 502, 503, 504],
  },
});

export interface Bill {
  congress: number;
  bill_type: string;
  number: number;
  title: string;
  summary?: string;
  status?: string;
  public_law_number?: string;
}

export interface BillDetail {
  bill: Bill;
  explanation?: string;
}

export interface FetchBillsParams {
  q?: string;
  status?: string;
  congress?: string;
  bill_type?: string;
  date_from?: string;
  date_to?: string;
  has_public_law?: boolean;
  sort_by?: string;
  sort_order?: string;
  page?: number;
  limit?: number;
}

export async function fetchBills(params?: FetchBillsParams) {
  const searchParams = new URLSearchParams();
  if (params?.q) searchParams.set('q', params.q);
  if (params?.status) searchParams.set('status', params.status);
  if (params?.congress) searchParams.set('congress', params.congress);
  if (params?.bill_type) searchParams.set('bill_type', params.bill_type);
  if (params?.date_from) searchParams.set('date_from', params.date_from);
  if (params?.date_to) searchParams.set('date_to', params.date_to);
  if (params?.has_public_law !== undefined) searchParams.set('has_public_law', params.has_public_law.toString());
  if (params?.sort_by) searchParams.set('sort_by', params.sort_by);
  if (params?.sort_order) searchParams.set('sort_order', params.sort_order);
  if (params?.page) searchParams.set('page', params.page.toString());
  if (params?.limit) searchParams.set('limit', params.limit.toString());

  return api.get('bills', { searchParams }).json<Bill[]>();
}

export async function fetchBillDetail(congress: number, billType: string, number: number) {
  return api.get(`bills/${congress}/${billType}/${number}`).json<BillDetail>();
}

export async function searchBills(q: string, page = 1) {
  return api.get('bills/search', { searchParams: { q, page } }).json<Bill[]>();
}
