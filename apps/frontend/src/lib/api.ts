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

export async function fetchBills(params?: { q?: string; status?: string; page?: number }) {
  const searchParams = new URLSearchParams();
  if (params?.q) searchParams.set('q', params.q);
  if (params?.status) searchParams.set('status', params.status);
  if (params?.page) searchParams.set('page', params.page.toString());
  
  return api.get('bills', { searchParams }).json<Bill[]>();
}

export async function fetchBillDetail(congress: number, billType: string, number: number) {
  return api.get(`bills/${congress}/${billType}/${number}`).json<BillDetail>();
}

export async function searchBills(q: string, page = 1) {
  return api.get('bills/search', { searchParams: { q, page } }).json<Bill[]>();
}
