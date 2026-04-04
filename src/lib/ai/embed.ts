import { embed } from "ai";
import { createHash } from "crypto";
import { getEmbeddingModel } from "./provider";

/**
 * Generate an embedding vector for bill content.
 * Always uses OpenAI text-embedding-3-small (1536 dimensions)
 * regardless of which provider generates explanations.
 */
export async function generateEmbedding(text: string): Promise<{
  vector: number[];
  contentHash: string;
  modelName: string;
}> {
  const model = getEmbeddingModel();

  const { embedding } = await embed({
    model,
    value: text,
  });

  const contentHash = createHash("sha256").update(text).digest("hex");

  return {
    vector: embedding,
    contentHash,
    modelName: "text-embedding-3-small",
  };
}

/**
 * Build the text to embed for a bill.
 * Combines title + explanation for richer semantic search.
 */
export function buildEmbeddingText(
  title: string,
  explanation?: string | null
): string {
  const parts = [title];
  if (explanation) {
    // Truncate explanation to ~500 words to keep embedding focused
    const words = explanation.split(/\s+/).slice(0, 500);
    parts.push(words.join(" "));
  }
  return parts.join("\n\n");
}
