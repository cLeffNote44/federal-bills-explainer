import type { bills, explanations, bookmarks, billTracking, comments, billTopics } from "@/lib/db/schema";
import type { InferSelectModel } from "drizzle-orm";

// ─── Database Types ───────────────────────────────────

export type Bill = InferSelectModel<typeof bills>;
export type Explanation = InferSelectModel<typeof explanations>;
export type Bookmark = InferSelectModel<typeof bookmarks>;
export type BillTracking = InferSelectModel<typeof billTracking>;
export type Comment = InferSelectModel<typeof comments>;
export type BillTopic = InferSelectModel<typeof billTopics>;

// ─── API Response Types ───────────────────────────────

export interface BillWithExplanation extends Bill {
  explanation?: Explanation | null;
  topics?: BillTopic[];
}

export interface BillListResponse {
  bills: Bill[];
  total: number;
  page: number;
  pageSize: number;
}

export interface CommentWithMeta extends Comment {
  displayName: string | null;
  upvoteCount: number;
  hasUpvoted?: boolean;
  replyCount: number;
}

export interface FeedbackStats {
  total: number;
  helpful: number;
  notHelpful: number;
  helpfulPercentage: number;
}

export interface TrackingUpdate {
  billId: string;
  congress: number;
  billType: string;
  number: number;
  title: string;
  updateType: "status_change" | "new_action";
  oldValue?: string;
  newValue: string;
  updateDate: string;
}

// ─── Sponsor Type ─────────────────────────────────────

export interface Sponsor {
  name: string;
  party: string;
  state: string;
  bioguideId?: string;
}
