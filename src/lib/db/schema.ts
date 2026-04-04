import {
  pgTable,
  uuid,
  text,
  integer,
  boolean,
  real,
  date,
  timestamp,
  jsonb,
  uniqueIndex,
  index,
  primaryKey,
  customType,
} from "drizzle-orm/pg-core";
import { relations } from "drizzle-orm";

// Custom pgvector type for Drizzle
const vector = customType<{ data: number[]; driverParam: string }>({
  dataType() {
    return "vector(1536)";
  },
  toDriver(value: number[]) {
    return `[${value.join(",")}]`;
  },
  fromDriver(value: unknown) {
    const str = String(value);
    return str
      .slice(1, -1)
      .split(",")
      .map(Number);
  },
});

// ─── Bills ────────────────────────────────────────────

export const bills = pgTable(
  "bills",
  {
    id: uuid("id").defaultRandom().primaryKey(),
    congress: integer("congress").notNull(),
    billType: text("bill_type").notNull(),
    number: integer("number").notNull(),
    title: text("title").notNull(),
    summary: text("summary"),
    status: text("status").notNull().default("introduced"),
    introducedDate: date("introduced_date"),
    latestActionDate: timestamp("latest_action_date", { withTimezone: true }),
    latestActionText: text("latest_action_text"),
    congressUrl: text("congress_url"),
    publicLawNumber: text("public_law_number"),
    sponsor: jsonb("sponsor").$type<{
      name: string;
      party: string;
      state: string;
      bioguideId?: string;
    }>(),
    cosponsorsCount: integer("cosponsors_count"),
    committees: jsonb("committees").$type<string[]>(),
    subjects: jsonb("subjects").$type<string[]>(),
    policyArea: text("policy_area"),
    textUrl: text("text_url"),
    version: integer("version").notNull().default(1),
    checksum: text("checksum"),
    lastFetchedAt: timestamp("last_fetched_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => [
    uniqueIndex("uq_bill_identity").on(
      table.congress,
      table.billType,
      table.number
    ),
    index("idx_bills_latest_action").on(table.latestActionDate),
    index("idx_bills_status").on(table.status),
    index("idx_bills_public_law").on(table.publicLawNumber),
    index("idx_bills_congress_type_number").on(
      table.congress,
      table.billType,
      table.number
    ),
  ]
);

// ─── Explanations ─────────────────────────────────────

export const explanations = pgTable(
  "explanations",
  {
    id: uuid("id").defaultRandom().primaryKey(),
    billId: uuid("bill_id")
      .notNull()
      .references(() => bills.id, { onDelete: "cascade" }),
    text: text("text").notNull(),
    simpleText: text("simple_text"),
    modelName: text("model_name").notNull(),
    modelProvider: text("model_provider").notNull(),
    version: integer("version").notNull().default(1),
    generatedAt: timestamp("generated_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => [index("idx_explanations_bill").on(table.billId)]
);

// ─── Embeddings ───────────────────────────────────────

export const embeddings = pgTable(
  "embeddings",
  {
    id: uuid("id").defaultRandom().primaryKey(),
    billId: uuid("bill_id")
      .notNull()
      .references(() => bills.id, { onDelete: "cascade" }),
    vector: vector("vector").notNull(),
    modelName: text("model_name").notNull(),
    contentHash: text("content_hash").notNull(),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => [
    uniqueIndex("uq_embedding_cache").on(table.contentHash, table.modelName),
  ]
);

// ─── User Profiles ────────────────────────────────────

export const userProfiles = pgTable("user_profiles", {
  id: uuid("id").primaryKey(), // FK to auth.users, set on trigger
  displayName: text("display_name"),
  zipCode: text("zip_code"),
  state: text("state"),
  emailNotifications: boolean("email_notifications").notNull().default(true),
  notificationFrequency: text("notification_frequency")
    .notNull()
    .default("daily"),
  preferences: jsonb("preferences").$type<Record<string, unknown>>(),
  createdAt: timestamp("created_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

// ─── Bookmarks ────────────────────────────────────────

export const bookmarks = pgTable(
  "bookmarks",
  {
    id: uuid("id").defaultRandom().primaryKey(),
    userId: uuid("user_id").notNull(),
    billId: uuid("bill_id")
      .notNull()
      .references(() => bills.id, { onDelete: "cascade" }),
    notes: text("notes"),
    folder: text("folder"),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => [
    uniqueIndex("uq_user_bill_bookmark").on(table.userId, table.billId),
    index("idx_bookmarks_user").on(table.userId),
  ]
);

// ─── Bill Tracking ────────────────────────────────────

export const billTracking = pgTable(
  "bill_tracking",
  {
    id: uuid("id").defaultRandom().primaryKey(),
    userId: uuid("user_id").notNull(),
    billId: uuid("bill_id")
      .notNull()
      .references(() => bills.id, { onDelete: "cascade" }),
    notifyOnStatusChange: boolean("notify_on_status_change")
      .notNull()
      .default(true),
    notifyOnVote: boolean("notify_on_vote").notNull().default(true),
    emailNotifications: boolean("email_notifications")
      .notNull()
      .default(false),
    lastKnownStatus: text("last_known_status"),
    lastNotifiedAt: timestamp("last_notified_at", { withTimezone: true }),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => [
    uniqueIndex("uq_user_bill_tracking").on(table.userId, table.billId),
    index("idx_tracking_user").on(table.userId),
  ]
);

// ─── Comments ─────────────────────────────────────────

export const comments = pgTable(
  "comments",
  {
    id: uuid("id").defaultRandom().primaryKey(),
    billId: uuid("bill_id")
      .notNull()
      .references(() => bills.id, { onDelete: "cascade" }),
    userId: uuid("user_id").notNull(),
    parentId: uuid("parent_id"),
    content: text("content").notNull(),
    isDeleted: boolean("is_deleted").notNull().default(false),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => [
    index("idx_comments_bill").on(table.billId),
    index("idx_comments_user").on(table.userId),
  ]
);

// ─── Comment Upvotes ──────────────────────────────────

export const commentUpvotes = pgTable(
  "comment_upvotes",
  {
    userId: uuid("user_id").notNull(),
    commentId: uuid("comment_id")
      .notNull()
      .references(() => comments.id, { onDelete: "cascade" }),
  },
  (table) => [primaryKey({ columns: [table.userId, table.commentId] })]
);

// ─── Explanation Feedback ─────────────────────────────

export const explanationFeedback = pgTable(
  "explanation_feedback",
  {
    id: uuid("id").defaultRandom().primaryKey(),
    explanationId: uuid("explanation_id")
      .notNull()
      .references(() => explanations.id, { onDelete: "cascade" }),
    userId: uuid("user_id"),
    sessionId: text("session_id"),
    isHelpful: boolean("is_helpful").notNull(),
    feedbackText: text("feedback_text"),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => [index("idx_feedback_explanation").on(table.explanationId)]
);

// ─── Bill Topics ──────────────────────────────────────

export const billTopics = pgTable(
  "bill_topics",
  {
    id: uuid("id").defaultRandom().primaryKey(),
    billId: uuid("bill_id")
      .notNull()
      .references(() => bills.id, { onDelete: "cascade" }),
    topicName: text("topic_name").notNull(),
    confidenceScore: real("confidence_score"),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => [
    uniqueIndex("uq_bill_topic").on(table.billId, table.topicName),
    index("idx_topics_name").on(table.topicName),
  ]
);

// ─── Ingestion Jobs ───────────────────────────────────

export const ingestionJobs = pgTable(
  "ingestion_jobs",
  {
    id: uuid("id").defaultRandom().primaryKey(),
    jobType: text("job_type").notNull(),
    status: text("status").notNull().default("pending"),
    config: jsonb("config").$type<Record<string, unknown>>(),
    totalRecords: integer("total_records").notNull().default(0),
    processedRecords: integer("processed_records").notNull().default(0),
    failedRecords: integer("failed_records").notNull().default(0),
    errorMessage: text("error_message"),
    startedAt: timestamp("started_at", { withTimezone: true }),
    completedAt: timestamp("completed_at", { withTimezone: true }),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => [
    index("idx_jobs_status").on(table.status),
    index("idx_jobs_created").on(table.createdAt),
  ]
);

// ─── Relations ────────────────────────────────────────

export const billsRelations = relations(bills, ({ many }) => ({
  explanations: many(explanations),
  embeddings: many(embeddings),
  bookmarks: many(bookmarks),
  tracking: many(billTracking),
  comments: many(comments),
  topics: many(billTopics),
}));

export const explanationsRelations = relations(explanations, ({ one, many }) => ({
  bill: one(bills, {
    fields: [explanations.billId],
    references: [bills.id],
  }),
  feedback: many(explanationFeedback),
}));

export const embeddingsRelations = relations(embeddings, ({ one }) => ({
  bill: one(bills, {
    fields: [embeddings.billId],
    references: [bills.id],
  }),
}));

export const bookmarksRelations = relations(bookmarks, ({ one }) => ({
  bill: one(bills, {
    fields: [bookmarks.billId],
    references: [bills.id],
  }),
}));

export const billTrackingRelations = relations(billTracking, ({ one }) => ({
  bill: one(bills, {
    fields: [billTracking.billId],
    references: [bills.id],
  }),
}));

export const commentsRelations = relations(comments, ({ one, many }) => ({
  bill: one(bills, {
    fields: [comments.billId],
    references: [bills.id],
  }),
  parent: one(comments, {
    fields: [comments.parentId],
    references: [comments.id],
    relationName: "replies",
  }),
  replies: many(comments, { relationName: "replies" }),
  upvotes: many(commentUpvotes),
}));

export const commentUpvotesRelations = relations(commentUpvotes, ({ one }) => ({
  comment: one(comments, {
    fields: [commentUpvotes.commentId],
    references: [comments.id],
  }),
}));

export const explanationFeedbackRelations = relations(
  explanationFeedback,
  ({ one }) => ({
    explanation: one(explanations, {
      fields: [explanationFeedback.explanationId],
      references: [explanations.id],
    }),
  })
);

export const billTopicsRelations = relations(billTopics, ({ one }) => ({
  bill: one(bills, {
    fields: [billTopics.billId],
    references: [bills.id],
  }),
}));
