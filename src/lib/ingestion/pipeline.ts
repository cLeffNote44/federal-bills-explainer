import { db } from "@/lib/db";
import { bills, explanations, billTopics, ingestionJobs } from "@/lib/db/schema";
import { eq } from "drizzle-orm";
import { fetchEnactedBills, getBillSummary } from "@/lib/congress/client";
import { generateBillExplanation } from "@/lib/ai/explain";
import { logger } from "@/lib/logger";
import type { CongressBillDetail } from "@/lib/congress/types";

interface IngestOptions {
  fromDate: string;
  toDate: string;
  maxRecords?: number;
}

interface IngestResult {
  jobId: string;
  billsProcessed: number;
  billsFailed: number;
  billsSkipped: number;
}

/**
 * Core ingestion pipeline. Designed to be called from:
 * - Vercel Cron handler (/api/cron/ingest)
 * - Admin trigger (/api/ingest)
 * - Future: Inngest step function
 */
export async function runIngestion(options: IngestOptions): Promise<IngestResult> {
  const [job] = await db
    .insert(ingestionJobs)
    .values({
      jobType: "sync",
      status: "running",
      config: { ...options },
      startedAt: new Date(),
    })
    .returning();

  const log = logger.child({ jobId: job.id, jobType: "sync" });
  log.info("Ingestion job started", { ...options });

  let processed = 0;
  let failed = 0;
  const skipped = 0;

  try {
    const congressBills = await fetchEnactedBills({
      fromDate: options.fromDate,
      toDate: options.toDate,
      maxRecords: options.maxRecords ?? 20,
    });

    log.info("Fetched bills from Congress.gov", { count: congressBills.length });

    for (const congressBill of congressBills) {
      const billRef = `${congressBill.type}-${congressBill.number}`;
      try {
        await processSingleBill(congressBill);
        processed++;
        log.debug("Bill processed", { bill: billRef });
      } catch (error) {
        log.error("Bill processing failed", error, { bill: billRef });
        failed++;
      }
    }

    await db
      .update(ingestionJobs)
      .set({
        status: "completed",
        processedRecords: processed,
        failedRecords: failed,
        totalRecords: congressBills.length,
        completedAt: new Date(),
      })
      .where(eq(ingestionJobs.id, job.id));

    log.info("Ingestion job completed", { processed, failed, skipped });
  } catch (error) {
    await db
      .update(ingestionJobs)
      .set({
        status: "failed",
        processedRecords: processed,
        failedRecords: failed,
        errorMessage: error instanceof Error ? error.message : "Unknown error",
        completedAt: new Date(),
      })
      .where(eq(ingestionJobs.id, job.id));
    log.error("Ingestion job failed", error, { processed, failed });
    throw error;
  }

  return {
    jobId: job.id,
    billsProcessed: processed,
    billsFailed: failed,
    billsSkipped: skipped,
  };
}

async function processSingleBill(
  congressBill: CongressBillDetail["bill"]
): Promise<void> {
  const billType = congressBill.type.toLowerCase();
  const congress = congressBill.congress;
  const billNumber = congressBill.number;

  // Fetch summary if available
  const summaryResponse = await getBillSummary(congress, billType, billNumber);
  const summary = summaryResponse?.summaries?.[0]?.text ?? null;

  // Parse sponsor
  const rawSponsor = congressBill.sponsors?.item?.[0];
  const sponsor = rawSponsor
    ? {
        name: rawSponsor.fullName,
        party: rawSponsor.party,
        state: rawSponsor.state,
        bioguideId: rawSponsor.bioguideId,
      }
    : null;

  // Determine status
  const hasLaw = congressBill.laws?.item?.length;
  const status = hasLaw ? "became_law" : "introduced";
  const publicLawNumber = hasLaw
    ? `${congressBill.laws!.item[0].type}-${congressBill.laws!.item[0].number}`
    : null;

  // Upsert bill
  const [bill] = await db
    .insert(bills)
    .values({
      congress,
      billType,
      number: billNumber,
      title: congressBill.title,
      summary,
      status,
      introducedDate: congressBill.introducedDate ?? null,
      latestActionDate: congressBill.latestAction?.actionDate
        ? new Date(congressBill.latestAction.actionDate)
        : null,
      latestActionText: congressBill.latestAction?.text ?? null,
      congressUrl: `https://www.congress.gov/bill/${congress}th-congress/${billType}/${billNumber}`,
      publicLawNumber,
      sponsor,
      cosponsorsCount: congressBill.cosponsors?.count ?? null,
      committees: congressBill.committees?.item?.map((c) => c.name) ?? null,
      subjects:
        congressBill.subjects?.legislativeSubjects?.map((s) => s.name) ?? null,
      policyArea: congressBill.policyArea?.name ?? null,
      lastFetchedAt: new Date(),
    })
    .onConflictDoUpdate({
      target: [bills.congress, bills.billType, bills.number],
      set: {
        title: congressBill.title,
        summary,
        status,
        latestActionDate: congressBill.latestAction?.actionDate
          ? new Date(congressBill.latestAction.actionDate)
          : null,
        latestActionText: congressBill.latestAction?.text ?? null,
        publicLawNumber,
        sponsor,
        cosponsorsCount: congressBill.cosponsors?.count ?? null,
        committees:
          congressBill.committees?.item?.map((c) => c.name) ?? null,
        subjects:
          congressBill.subjects?.legislativeSubjects?.map((s) => s.name) ??
          null,
        policyArea: congressBill.policyArea?.name ?? null,
        lastFetchedAt: new Date(),
        updatedAt: new Date(),
        version: 1, // TODO: increment
      },
    })
    .returning();

  // Generate AI explanation
  const explanationResult = await generateBillExplanation({
    title: bill.title,
    summary: bill.summary,
    sponsor: bill.sponsor,
    policyArea: bill.policyArea,
    status: bill.status,
    billType: bill.billType,
    number: bill.number,
    congress: bill.congress,
  });

  // Upsert explanation
  const existingExplanation = await db.query.explanations.findFirst({
    where: eq(explanations.billId, bill.id),
  });

  if (existingExplanation) {
    await db
      .update(explanations)
      .set({
        text: explanationResult.text,
        simpleText: explanationResult.simpleText,
        modelName: explanationResult.modelName,
        modelProvider: explanationResult.modelProvider,
        version: existingExplanation.version + 1,
        generatedAt: new Date(),
      })
      .where(eq(explanations.id, existingExplanation.id));
  } else {
    await db.insert(explanations).values({
      billId: bill.id,
      text: explanationResult.text,
      simpleText: explanationResult.simpleText,
      modelName: explanationResult.modelName,
      modelProvider: explanationResult.modelProvider,
    });
  }

  // Upsert topics
  for (const topic of explanationResult.topics) {
    await db
      .insert(billTopics)
      .values({
        billId: bill.id,
        topicName: topic.name,
        confidenceScore: topic.confidence,
      })
      .onConflictDoUpdate({
        target: [billTopics.billId, billTopics.topicName],
        set: {
          confidenceScore: topic.confidence,
        },
      });
  }
}
