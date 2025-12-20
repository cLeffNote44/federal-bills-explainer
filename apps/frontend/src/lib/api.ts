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

// Topics API
export interface Topic {
  name: string;
  count: number;
}

export async function fetchTopics(): Promise<Topic[]> {
  return api.get('topics').json<Topic[]>();
}

export async function fetchTopicBills(topicName: string, page = 1, pageSize = 20) {
  return api.get(`topics/${encodeURIComponent(topicName)}/bills`, {
    searchParams: { page, page_size: pageSize }
  }).json<Bill[]>();
}

// Feedback API
export interface FeedbackData {
  explanation_id: string;
  bill_id: string;
  is_helpful: boolean;
  feedback_text?: string;
  session_id?: string;
}

export async function submitFeedback(data: FeedbackData, token?: string) {
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return api.post('feedback', { json: data, headers }).json();
}

export async function getFeedbackStats(explanationId: string) {
  return api.get(`feedback/stats/${explanationId}`).json<{
    helpful_count: number;
    not_helpful_count: number;
  }>();
}

// Bookmarks API
export interface BookmarkData {
  bill_id: string;
  congress: number;
  bill_type: string;
  number: number;
  notes?: string;
  folder?: string;
}

export async function createBookmark(data: BookmarkData, token: string) {
  return api.post('bookmarks', {
    json: data,
    headers: { 'Authorization': `Bearer ${token}` }
  }).json();
}

export async function getBookmarks(token: string, folder?: string) {
  const searchParams: Record<string, string> = {};
  if (folder) searchParams.folder = folder;
  return api.get('bookmarks', {
    searchParams,
    headers: { 'Authorization': `Bearer ${token}` }
  }).json();
}

export async function checkBookmark(congress: number, billType: string, number: number, token: string) {
  return api.get(`bookmarks/check/${congress}/${billType}/${number}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }).json<{ is_bookmarked: boolean; bookmark_id?: string }>();
}

export async function deleteBookmark(congress: number, billType: string, number: number, token: string) {
  return api.delete(`bookmarks/${congress}/${billType}/${number}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }).json();
}

// Tracking API
export interface TrackingData {
  congress: number;
  bill_type: string;
  number: number;
  notify_on_status_change?: boolean;
  notify_on_vote?: boolean;
  notify_on_amendments?: boolean;
  email_notifications?: boolean;
}

export async function trackBill(data: TrackingData, token: string) {
  return api.post('tracking', {
    json: data,
    headers: { 'Authorization': `Bearer ${token}` }
  }).json();
}

export async function getTrackedBills(token: string) {
  return api.get('tracking', {
    headers: { 'Authorization': `Bearer ${token}` }
  }).json();
}

export async function checkTracking(congress: number, billType: string, number: number, token: string) {
  return api.get(`tracking/check/${congress}/${billType}/${number}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }).json<{ is_tracking: boolean; tracking_id?: string }>();
}

export async function stopTracking(congress: number, billType: string, number: number, token: string) {
  return api.delete(`tracking/${congress}/${billType}/${number}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }).json();
}

// Comments API
export interface CommentData {
  content: string;
  parent_id?: string;
}

export async function createComment(
  congress: number,
  billType: string,
  number: number,
  data: CommentData,
  token: string
) {
  return api.post(`comments/${congress}/${billType}/${number}`, {
    json: data,
    headers: { 'Authorization': `Bearer ${token}` }
  }).json();
}

export async function getComments(
  congress: number,
  billType: string,
  number: number,
  page = 1,
  sortBy = 'newest'
) {
  return api.get(`comments/${congress}/${billType}/${number}`, {
    searchParams: { page, sort_by: sortBy }
  }).json();
}

export async function upvoteComment(
  congress: number,
  billType: string,
  number: number,
  commentId: string,
  token: string
) {
  return api.post(`comments/${congress}/${billType}/${number}/${commentId}/upvote`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }).json();
}

// Auth API
export interface LoginData {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  display_name?: string;
}

export async function login(data: LoginData) {
  return api.post('auth/login', { json: data }).json<{
    access_token: string;
    user: { id: string; email: string; display_name?: string };
  }>();
}

export async function register(data: RegisterData) {
  return api.post('auth/register', { json: data }).json<{
    access_token: string;
    user: { id: string; email: string; display_name?: string };
  }>();
}

export async function getProfile(token: string) {
  return api.get('auth/profile', {
    headers: { 'Authorization': `Bearer ${token}` }
  }).json();
}

// Related Bills API
export async function getRelatedBills(
  congress: number,
  billType: string,
  number: number,
  limit = 5
) {
  return api.get(`bills/${congress}/${billType}/${number}/related`, {
    searchParams: { limit }
  }).json<Bill[]>();
}

// Bill Timeline API
export interface TimelineEvent {
  date: string;
  type: 'introduced' | 'committee' | 'vote' | 'passed' | 'signed' | 'vetoed';
  title: string;
  description?: string;
}

export async function getBillTimeline(
  congress: number,
  billType: string,
  number: number
) {
  return api.get(`bills/${congress}/${billType}/${number}/timeline`).json<TimelineEvent[]>();
}
