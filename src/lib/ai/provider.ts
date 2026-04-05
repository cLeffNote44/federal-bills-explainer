import { anthropic } from "@ai-sdk/anthropic";

type AIProvider = "claude" | "ollama";

function getProvider(): AIProvider {
  return (process.env.AI_PROVIDER as AIProvider) ?? "claude";
}

/**
 * Returns the language model for generating explanations.
 * Claude in production, Ollama for local dev — same AI SDK interface.
 */
export async function getExplanationModel() {
  const provider = getProvider();

  if (provider === "ollama") {
    // Ollama uses OpenAI-compatible API via AI SDK
    const { createOpenAI } = await import("@ai-sdk/openai");
    const ollama = createOpenAI({
      baseURL: process.env.OLLAMA_BASE_URL + "/v1",
      apiKey: "ollama",
    });
    return ollama(process.env.OLLAMA_MODEL ?? "llama3.1");
  }

  // Default: Claude
  return anthropic("claude-sonnet-4-5-20250514");
}
