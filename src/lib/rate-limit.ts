import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

interface Bucket {
  count: number;
  resetAt: number;
}

// In-memory bucket store. Per-serverless-instance only — replace with
// Upstash Redis or Vercel KV for production-grade global rate limiting.
const buckets = new Map<string, Bucket>();

// Bound the map size to avoid unbounded memory growth on long-running instances.
const MAX_KEYS = 10_000;

function evictExpired(now: number) {
  if (buckets.size < MAX_KEYS) return;
  for (const [key, bucket] of buckets) {
    if (bucket.resetAt < now) buckets.delete(key);
    if (buckets.size < MAX_KEYS / 2) break;
  }
}

export interface RateLimitResult {
  ok: boolean;
  remaining: number;
  resetAt: number;
}

export function rateLimit(
  key: string,
  limit: number,
  windowMs: number
): RateLimitResult {
  const now = Date.now();
  evictExpired(now);

  const bucket = buckets.get(key);
  if (!bucket || bucket.resetAt < now) {
    const resetAt = now + windowMs;
    buckets.set(key, { count: 1, resetAt });
    return { ok: true, remaining: limit - 1, resetAt };
  }

  if (bucket.count >= limit) {
    return { ok: false, remaining: 0, resetAt: bucket.resetAt };
  }

  bucket.count++;
  return { ok: true, remaining: limit - bucket.count, resetAt: bucket.resetAt };
}

export function getClientId(request: NextRequest): string {
  const forwarded = request.headers.get("x-forwarded-for");
  if (forwarded) return forwarded.split(",")[0]!.trim();
  return request.headers.get("x-real-ip") ?? "unknown";
}

/**
 * Apply a per-route rate limit. Returns a 429 response if the client is
 * over the limit, otherwise returns null and the caller proceeds.
 */
export function enforceRateLimit(
  request: NextRequest,
  options: { route: string; limit: number; windowMs: number; clientId?: string }
): NextResponse | null {
  const id = options.clientId ?? getClientId(request);
  const key = `${options.route}:${id}`;
  const result = rateLimit(key, options.limit, options.windowMs);

  if (!result.ok) {
    return NextResponse.json(
      { error: "Too many requests. Please slow down." },
      {
        status: 429,
        headers: {
          "Retry-After": String(
            Math.max(1, Math.ceil((result.resetAt - Date.now()) / 1000))
          ),
          "X-RateLimit-Limit": String(options.limit),
          "X-RateLimit-Remaining": "0",
          "X-RateLimit-Reset": String(Math.ceil(result.resetAt / 1000)),
        },
      }
    );
  }

  return null;
}
