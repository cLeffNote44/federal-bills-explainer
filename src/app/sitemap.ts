import { db } from "@/lib/db";
import { bills, billTopics } from "@/lib/db/schema";
import type { MetadataRoute } from "next";

// Force dynamic — sitemap needs DB access at request time, not build time
export const dynamic = "force-dynamic";

const BASE_URL = process.env.NEXT_PUBLIC_APP_URL ?? "https://federalbills.app";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  // If no DATABASE_URL, return static pages only
  if (!process.env.DATABASE_URL) {
    return [
      { url: BASE_URL, changeFrequency: "daily", priority: 1 },
      { url: `${BASE_URL}/topics`, changeFrequency: "weekly", priority: 0.8 },
    ];
  }

  // Static pages
  const staticPages: MetadataRoute.Sitemap = [
    { url: BASE_URL, changeFrequency: "daily", priority: 1 },
    { url: `${BASE_URL}/topics`, changeFrequency: "weekly", priority: 0.8 },
    { url: `${BASE_URL}/login`, changeFrequency: "yearly", priority: 0.3 },
    { url: `${BASE_URL}/register`, changeFrequency: "yearly", priority: 0.3 },
  ];

  // Dynamic bill pages
  const allBills = await db
    .select({
      congress: bills.congress,
      billType: bills.billType,
      number: bills.number,
      updatedAt: bills.updatedAt,
    })
    .from(bills)
    .limit(5000);

  const billPages: MetadataRoute.Sitemap = allBills.map((bill) => ({
    url: `${BASE_URL}/bills/${bill.congress}/${bill.billType}/${bill.number}`,
    lastModified: bill.updatedAt,
    changeFrequency: "weekly" as const,
    priority: 0.7,
  }));

  // Topic pages
  const topics = await db
    .selectDistinct({ name: billTopics.topicName })
    .from(billTopics);

  const topicPages: MetadataRoute.Sitemap = topics.map((t) => ({
    url: `${BASE_URL}/topics/${encodeURIComponent(t.name)}`,
    changeFrequency: "weekly" as const,
    priority: 0.6,
  }));

  return [...staticPages, ...billPages, ...topicPages];
}
