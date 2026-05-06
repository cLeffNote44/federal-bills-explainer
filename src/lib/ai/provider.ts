import { anthropic } from "@ai-sdk/anthropic";

type AIProvider = "claude" | "ollama";

export const CLAUDE_MODEL = "claude-sonnet-4-6";

function getProvider(): AIProvider {
  return (process.env.AI_PROVIDER as AIProvider) ?? "claude";
}

export interface ResolvedModel {
  model: Awaited<ReturnType<typeof anthropic>> | ReturnType<ReturnType<typeof import("@ai-sdk/openai").createOpenAI>>;
  modelName: string;
  modelProvider: AIProvider;
}

/**
 * Returns the language model for generating explanations along with
 * provenance metadata so callers can record which model produced output.
 */
export async function getExplanationModel(): Promise<ResolvedModel> {
  const provider = getProvider();

  if (provider === "ollama") {
    const { createOpenAI } = await import("@ai-sdk/openai");
    const ollama = createOpenAI({
      baseURL: process.env.OLLAMA_BASE_URL + "/v1",
      apiKey: "ollama",
    });
    const modelName = process.env.OLLAMA_MODEL ?? "llama3.1";
    return { model: ollama(modelName), modelName, modelProvider: "ollama" };
  }

  return {
    model: anthropic(CLAUDE_MODEL),
    modelName: CLAUDE_MODEL,
    modelProvider: "claude",
  };
}
