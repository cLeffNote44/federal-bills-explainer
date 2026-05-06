# Federal Bills Explainer

> AI-powered platform that makes federal legislation accessible through plain-language explanations and semantic search.

**Did you also take a look at the "Big Beautiful Bill (bloat)" and think, what in the name of??....**
**Yeah well I did too. So I built this to help the fool in all of us understand what it is they do in washington**
**...or at least try**

## Tech Stack

- **Next.js 16** (App Router) + TypeScript
- **Supabase** (Postgres 17 + Auth + RLS)
- **Drizzle ORM**
- **Claude API** (production) + **Ollama** (local dev) via Vercel AI SDK
- **Postgres full-text search** (weighted tsvector on title/summary/policy_area)
- **Tailwind CSS 4** + shadcn/ui
- **Vercel** deployment

## Quick Start

```bash
# Clone and install
git clone https://github.com/cLeffNote44/federal-bills-explainer.git
cd federal-bills-explainer
pnpm install

# Configure environment
cp .env.example .env.local
# Fill in your Supabase, API keys, etc.

# Start dev server
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000).

## Features

- Browse and filter federal bills
- Postgres full-text search with weighted ranking (title > summary > policy area)
- AI-generated plain-language explanations (full + ELI5)
- User accounts (Supabase Auth) with profile + notification preferences
- Bookmark and organize bills
- Track bills for status updates
- Community comments with nested replies
- Explanation feedback (helpful/not helpful)
- Topic-based browsing
- CSV/JSON export (authenticated)
- Dark mode

## Development

```bash
pnpm dev          # Start dev server (Turbopack)
pnpm build        # Production build
pnpm lint         # ESLint
pnpm type-check   # TypeScript check
pnpm test         # Vitest
pnpm db:generate  # Generate Drizzle migration
pnpm db:push      # Push schema to database
pnpm db:studio    # Open Drizzle Studio
```

## AI Providers

Set `AI_PROVIDER` in `.env.local`:
- `claude` (default) — Uses Claude API (`claude-sonnet-4-6`) for high-quality explanations
- `ollama` — Uses local Ollama for free development

## Search

Uses the `search_bills_fts(search_query, match_count, page_offset)` Postgres function, which ranks results by `ts_rank` over a weighted `tsvector` column on the `bills` table (title=A, summary=B, policy_area=C).

## Database

Migrations live in `supabase/migrations/` and are applied via the Supabase CLI or MCP. Drizzle schema (`src/lib/db/schema.ts`) is the source of truth for application code.

## License

MIT
