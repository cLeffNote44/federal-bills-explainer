import { describe, it, expect } from "vitest";
import {
  billListQuery,
  billPathParams,
  createBookmarkBody,
  createCommentBody,
  submitFeedbackBody,
  semanticSearchQuery,
  exportQuery,
} from "./validators";

describe("billListQuery", () => {
  it("parses defaults correctly", () => {
    const result = billListQuery.parse({});
    expect(result.page).toBe(1);
    expect(result.pageSize).toBe(20);
    expect(result.sortBy).toBe("date");
    expect(result.sortOrder).toBe("desc");
  });

  it("coerces string numbers", () => {
    const result = billListQuery.parse({ page: "3", pageSize: "10" });
    expect(result.page).toBe(3);
    expect(result.pageSize).toBe(10);
  });

  it("validates status enum", () => {
    const result = billListQuery.parse({ status: "became_law" });
    expect(result.status).toBe("became_law");
  });

  it("rejects invalid status", () => {
    expect(() => billListQuery.parse({ status: "invalid" })).toThrow();
  });

  it("caps pageSize at 50", () => {
    expect(() => billListQuery.parse({ pageSize: "100" })).toThrow();
  });
});

describe("billPathParams", () => {
  it("parses valid params", () => {
    const result = billPathParams.parse({
      congress: "118",
      billType: "hr",
      number: "1234",
    });
    expect(result.congress).toBe(118);
    expect(result.billType).toBe("hr");
    expect(result.number).toBe(1234);
  });

  it("rejects invalid bill type", () => {
    expect(() =>
      billPathParams.parse({ congress: "118", billType: "invalid", number: "1" })
    ).toThrow();
  });
});

describe("createBookmarkBody", () => {
  it("requires billId as uuid", () => {
    expect(() => createBookmarkBody.parse({ billId: "not-uuid" })).toThrow();
  });

  it("accepts valid bookmark", () => {
    const result = createBookmarkBody.parse({
      billId: "550e8400-e29b-41d4-a716-446655440000",
      notes: "Important bill",
      folder: "Climate",
    });
    expect(result.notes).toBe("Important bill");
  });
});

describe("createCommentBody", () => {
  it("requires content between 1 and 5000 chars", () => {
    expect(() => createCommentBody.parse({ content: "" })).toThrow();
    const result = createCommentBody.parse({ content: "Good bill" });
    expect(result.content).toBe("Good bill");
  });

  it("rejects content over 5000 chars", () => {
    expect(() =>
      createCommentBody.parse({ content: "x".repeat(5001) })
    ).toThrow();
  });
});

describe("submitFeedbackBody", () => {
  it("requires explanationId and isHelpful", () => {
    const result = submitFeedbackBody.parse({
      explanationId: "550e8400-e29b-41d4-a716-446655440000",
      isHelpful: true,
    });
    expect(result.isHelpful).toBe(true);
  });
});

describe("semanticSearchQuery", () => {
  it("requires minimum 3 character query", () => {
    expect(() => semanticSearchQuery.parse({ q: "ab" })).toThrow();
    const result = semanticSearchQuery.parse({ q: "climate change" });
    expect(result.q).toBe("climate change");
  });
});

describe("exportQuery", () => {
  it("defaults to json format and 100 limit", () => {
    const result = exportQuery.parse({});
    expect(result.format).toBe("json");
    expect(result.limit).toBe(100);
    expect(result.includeExplanations).toBe(false);
  });

  it("caps limit at 1000", () => {
    expect(() => exportQuery.parse({ limit: "2000" })).toThrow();
  });
});
