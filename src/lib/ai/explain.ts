import { generateObject, generateText } from "ai";
import { z } from "zod";
import { getExplanationModel } from "./provider";

const SYSTEM_PROMPT = `You are a civic education expert who explains US federal legislation in plain language.
Your goal is to help everyday Americans understand what bills do, who they affect, and why they matter.
Be accurate, non-partisan, and accessible. Avoid legal jargon. Use concrete examples when possible.`;

export interface BillInput {
  title: string;
  summary?: string | null;
  sponsor?: { name: string; party: string; state: string } | null;
  policyArea?: string | null;
  status?: string | null;
  billType: string;
  number: number;
  congress: number;
}

export interface ExplanationResult {
  text: string;
  simpleText: string;
  topics: { name: string; confidence: number }[];
}

export async function generateBillExplanation(
  bill: BillInput
): Promise<ExplanationResult> {
  const model = await getExplanationModel();

  const billContext = [
    `Bill: ${bill.billType.toUpperCase()}-${bill.number} (${bill.congress}th Congress)`,
    `Title: ${bill.title}`,
    bill.summary ? `Summary: ${bill.summary}` : null,
    bill.sponsor
      ? `Sponsor: ${bill.sponsor.name} (${bill.sponsor.party}-${bill.sponsor.state})`
      : null,
    bill.policyArea ? `Policy Area: ${bill.policyArea}` : null,
    bill.status ? `Status: ${bill.status}` : null,
  ]
    .filter(Boolean)
    .join("\n");

  // Generate full explanation + ELI5 in one call
  const { text: fullText } = await generateText({
    model,
    system: SYSTEM_PROMPT,
    prompt: `Explain this federal bill in two sections:

SECTION 1 - FULL EXPLANATION (300-500 words):
Write a clear, thorough explanation of what this bill does, who it affects, and why it matters.

SECTION 2 - SIMPLE EXPLANATION (under 100 words):
Write an ELI5 (Explain Like I'm 5) version using the simplest possible language.

Separate the sections with "---ELI5---"

${billContext}`,
  });

  const [explanation, eli5] = fullText.split("---ELI5---").map((s) => s.trim());

  // Generate topic classifications
  const { object: topicResult } = await generateObject({
    model,
    system:
      "You classify US federal bills into topic categories. Return 2-5 relevant topics with confidence scores.",
    prompt: `Classify this bill into topics:\n\n${billContext}`,
    schema: z.object({
      topics: z.array(
        z.object({
          name: z.string().describe("Topic category name"),
          confidence: z
            .number()
            .min(0)
            .max(1)
            .describe("Confidence score 0-1"),
        })
      ),
    }),
  });

  return {
    text: explanation || fullText,
    simpleText: eli5 || "",
    topics: topicResult.topics,
  };
}
