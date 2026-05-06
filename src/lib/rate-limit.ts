import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

interface Bucket {
  count: number;
  resetAt: number;
}

// In-memory bucket store. Per-serverless-instance only — used as the default
// backend and as a fallback when Upstash is unavailable.
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

function rateLimitMemory(
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

/**
 * Upstash REST-backed rate limiter (fixed-window via INCR + PEXPIRE NX).
 * Returns null if Upstash isn't configured or the call fails — caller should
 * fall back to the in-memory limiter.
 */
async function rateLimitUpstash(
  key: string,
  limit: number,
  windowMs: number
): Promise<RateLimitResult | null> {
  const url = process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.UPSTASH_REDIS_REST_TOKEN;
  if (!url || !token) return null;

  try {
    const res = await fetch(url + "/pipeline", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify([
        ["INCR", key],
        ["PEXPIRE", key, windowMs, "NX"],
        ["PTTL", key],
      ]),
      // Tight timeout: rate limiting must not become a tail-latency problem.
      signal: AbortSignal.timeout(500),
    });

    if (!res.ok) return null;

    const data = (await res.json()) as Array<{ result: number }>;
    const count = data[0]?.result ?? 0;
    const ttlMs = data[2]?.result ?? windowMs;
    const resetAt = Date.now() + (ttlMs > 0 ? ttlMs : windowMs);

    if (count > limit) {
      return { ok: false, remaining: 0, resetAt };
    }
    return { ok: true, remaining: Math.max(0, limit - count), resetAt };
  } catch {
    return null;
  }
}

export async function rateLimit(
  key: string,
  limit: number,
  windowMs: number
): Promise<RateLimitResult> {
  const upstash = await rateLimitUpstash(key, limit, windowMs);
  if (upstash) return upstash;
  return rateLimitMemory(key, limit, windowMs);
}

export function getClientId(request: NextRequest): string {
  const forwarded = request.headers.get("x-forwarded-for");
  if (forwarded) return forwarded.split(",")[0]!.trim();
  return request.headers.get("x-real-ip") ?? "unknown";
}

/**
 * Apply a per-route rate limit. Returns a 429 response if the client is
 * over the limit, otherwise returns null and the caller proceeds.
 *
 * Uses Upstash Redis (UPSTASH_REDIS_REST_URL + UPSTASH_REDIS_REST_TOKEN)
 * when configured for global limiting, falling back to per-instance
 * in-memory buckets otherwise.
 */
export async function enforceRateLimit(
  request: NextRequest,
  options: { route: string; limit: number; windowMs: number; clientId?: string }
): Promise<NextResponse | null> {
  const id = options.clientId ?? getClientId(request);
  const key = `rl:${options.route}:${id}`;
  const result = await rateLimit(key, options.limit, options.windowMs);

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
