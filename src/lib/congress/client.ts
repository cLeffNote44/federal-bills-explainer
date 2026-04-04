import type {
  CongressBillListResponse,
  CongressBillDetail,
  CongressBillSummaryResponse,
} from "./types";

const BASE_URL = "https://api.congress.gov/v3";
const RATE_LIMIT_MS = 1000; // 1 request per second

let lastRequestTime = 0;

async function rateLimitedFetch(url: string): Promise<Response> {
  const now = Date.now();
  const elapsed = now - lastRequestTime;
  if (elapsed < RATE_LIMIT_MS) {
    await new Promise((r) => setTimeout(r, RATE_LIMIT_MS - elapsed));
  }
  lastRequestTime = Date.now();

  const response = await fetch(url, {
    headers: {
      "X-Api-Key": process.env.CONGRESS_API_KEY!,
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(
      `Congress API error: ${response.status} ${response.statusText}`
    );
  }

  return response;
}

export async function listBills(options: {
  fromDate?: string;
  toDate?: string;
  limit?: number;
  offset?: number;
  sort?: string;
}): Promise<CongressBillListResponse> {
  const params = new URLSearchParams({
    format: "json",
    limit: String(options.limit ?? 20),
    offset: String(options.offset ?? 0),
    sort: options.sort ?? "updateDate+desc",
  });

  if (options.fromDate) params.set("fromDateTime", `${options.fromDate}T00:00:00Z`);
  if (options.toDate) params.set("toDateTime", `${options.toDate}T23:59:59Z`);

  const res = await rateLimitedFetch(`${BASE_URL}/bill?${params}`);
  return res.json();
}

export async function getBillDetail(
  congress: number,
  billType: string,
  billNumber: number
): Promise<CongressBillDetail> {
  const type = billType.toLowerCase();
  const res = await rateLimitedFetch(
    `${BASE_URL}/bill/${congress}/${type}/${billNumber}?format=json`
  );
  return res.json();
}

export async function getBillSummary(
  congress: number,
  billType: string,
  billNumber: number
): Promise<CongressBillSummaryResponse | null> {
  try {
    const type = billType.toLowerCase();
    const res = await rateLimitedFetch(
      `${BASE_URL}/bill/${congress}/${type}/${billNumber}/summaries?format=json`
    );
    return res.json();
  } catch {
    return null;
  }
}

/**
 * Fetch enacted bills (became law) within a date range.
 */
export async function fetchEnactedBills(options: {
  fromDate: string;
  toDate: string;
  maxRecords?: number;
}): Promise<CongressBillDetail["bill"][]> {
  const bills: CongressBillDetail["bill"][] = [];
  const limit = options.maxRecords ?? 50;
  let offset = 0;
  let hasMore = true;

  while (hasMore && bills.length < limit) {
    const listResponse = await listBills({
      fromDate: options.fromDate,
      toDate: options.toDate,
      limit: Math.min(20, limit - bills.length),
      offset,
    });

    for (const summary of listResponse.bills) {
      if (bills.length >= limit) break;

      const detail = await getBillDetail(
        summary.congress,
        summary.type,
        summary.number
      );

      bills.push(detail.bill);
    }

    hasMore = !!listResponse.pagination.next;
    offset += listResponse.bills.length;
  }

  return bills;
}
