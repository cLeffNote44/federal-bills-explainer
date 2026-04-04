import { z } from "zod";

// ─── Bill Types ───────────────────────────────────────

export const BILL_TYPES = [
  "hr",
  "s",
  "hjres",
  "sjres",
  "hconres",
  "sconres",
  "hres",
  "sres",
] as const;

export const BILL_STATUSES = [
  "introduced",
  "in_committee",
  "passed_house",
  "passed_senate",
  "enrolled",
  "vetoed",
  "became_law",
] as const;

// ─── API Query Schemas ────────────────────────────────

export const billListQuery = z.object({
  q: z.string().optional(),
  status: z.enum(BILL_STATUSES).optional(),
  congress: z.coerce.number().int().min(1).optional(),
  billType: z.enum(BILL_TYPES).optional(),
  dateFrom: z.string().date().optional(),
  dateTo: z.string().date().optional(),
  page: z.coerce.number().int().min(1).default(1),
  pageSize: z.coerce.number().int().min(1).max(50).default(20),
  sortBy: z.enum(["date", "congress", "number"]).default("date"),
  sortOrder: z.enum(["asc", "desc"]).default("desc"),
});

export const semanticSearchQuery = z.object({
  q: z.string().min(3),
  page: z.coerce.number().int().min(1).default(1),
  pageSize: z.coerce.number().int().min(1).max(50).default(20),
});

export const billPathParams = z.object({
  congress: z.coerce.number().int().min(1),
  billType: z.enum(BILL_TYPES),
  number: z.coerce.number().int().min(1),
});

// ─── User Input Schemas ───────────────────────────────

export const createBookmarkBody = z.object({
  billId: z.string().uuid(),
  notes: z.string().max(1000).optional(),
  folder: z.string().max(100).optional(),
});

export const createTrackingBody = z.object({
  billId: z.string().uuid(),
  notifyOnStatusChange: z.boolean().default(true),
  notifyOnVote: z.boolean().default(true),
  emailNotifications: z.boolean().default(false),
});

export const updateTrackingBody = z.object({
  notifyOnStatusChange: z.boolean().optional(),
  notifyOnVote: z.boolean().optional(),
  emailNotifications: z.boolean().optional(),
});

export const createCommentBody = z.object({
  content: z.string().min(1).max(5000),
  parentId: z.string().uuid().optional(),
});

export const updateCommentBody = z.object({
  content: z.string().min(1).max(5000),
});

export const submitFeedbackBody = z.object({
  explanationId: z.string().uuid(),
  isHelpful: z.boolean(),
  feedbackText: z.string().max(2000).optional(),
  sessionId: z.string().optional(),
});

export const updateProfileBody = z.object({
  displayName: z.string().max(100).optional(),
  emailNotifications: z.boolean().optional(),
  notificationFrequency: z.enum(["realtime", "daily", "weekly"]).optional(),
  zipCode: z.string().max(10).optional(),
  state: z.string().max(2).optional(),
});

export const exportQuery = z.object({
  format: z.enum(["csv", "json"]).default("json"),
  includeExplanations: z.coerce.boolean().default(false),
  limit: z.coerce.number().int().min(1).max(1000).default(100),
  congress: z.coerce.number().int().optional(),
  status: z.enum(BILL_STATUSES).optional(),
});
