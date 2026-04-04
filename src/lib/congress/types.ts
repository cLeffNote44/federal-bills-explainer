// Congress.gov API response types

export interface CongressBillListResponse {
  bills: CongressBillSummary[];
  pagination: {
    count: number;
    next?: string;
  };
}

export interface CongressBillSummary {
  congress: number;
  type: string; // "HR", "S", "HJRES", etc.
  number: number;
  title: string;
  latestAction?: {
    actionDate: string;
    text: string;
  };
  url: string;
  updateDate: string;
}

export interface CongressBillDetail {
  bill: {
    congress: number;
    type: string;
    number: number;
    title: string;
    introducedDate?: string;
    policyArea?: { name: string };
    subjects?: {
      legislativeSubjects: { name: string }[];
    };
    sponsors?: {
      item: {
        bioguideId: string;
        fullName: string;
        party: string;
        state: string;
      }[];
    };
    cosponsors?: { count: number };
    committees?: {
      item: { name: string }[];
    };
    latestAction?: {
      actionDate: string;
      text: string;
    };
    laws?: {
      item: { number: string; type: string }[];
    };
    textVersions?: {
      url: string;
    };
    summaries?: {
      url: string;
    };
    actions?: {
      url: string;
    };
    cboCostEstimates?: unknown[];
  };
}

export interface CongressBillSummaryResponse {
  summaries: {
    text: string;
    actionDate: string;
    versionCode: string;
  }[];
}
