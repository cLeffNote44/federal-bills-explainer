import { anthropic } from "@ai-sdk/anthropic";
import { openai } from "@ai-sdk/openai";

type AIProvider = "claude" | "ollama";

function getProvider(): AIProvider {
  return (process.env.AI_PROVIDER as AIProvider) ?? "claude";
}

/**
 * Returns the language model for generating explanations.
 * Claude in production, Ollama for local dev — same AI SDK interface.
 */
export function getExplanationModel() {
  const provider = getProvider();

  if (provider === "ollama") {
    // Ollama uses OpenAI-compatible API via AI SDK
    const { createOpenAI } = require("@ai-sdk/openai");
    const ollama = createOpenAI({
      baseURL: process.env.OLLAMA_BASE_URL + "/v1",
      apiKey: "ollama", // Ollama doesn't need a real key
    });
    return ollama(process.env.OLLAMA_MODEL ?? "llama3.1");
  }

  // Default: Claude
  return anthropic("claude-sonnet-4-5-20250514");
}

/**
 * Returns the embedding model. Always OpenAI text-embedding-3-small
 * regardless of explanation provider — consistent vector space.
 */
export function getEmbeddingModel() {
  return openai.embedding("text-embedding-3-small");
}
