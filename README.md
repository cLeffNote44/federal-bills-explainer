# Federal Bills Explainer

> AI-powered platform that makes federal legislation accessible through plain-language explanations and semantic search.

**Did you also take a look at the "Big Beautiful Bill (bloat)" and think, what in the name of??....**
**Yeah well I did too. So I built this to help the fool in all of us understand what it is they do in washington**
**...or at least try**

## Tech Stack

- **Next.js 15** (App Router) + TypeScript
- **Supabase** (Postgres + pgvector + Auth + RLS)
- **Drizzle ORM**
- **Claude API** (production) + **Ollama** (local dev) via Vercel AI SDK
- **OpenAI** text-embedding-3-small for semantic search
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

- Browse and search federal bills
- AI-generated plain-language explanations (full + ELI5)
- Semantic vector search via pgvector
- User accounts (Supabase Auth)
- Bookmark and organize bills
- Track bills for status updates
- Community comments with nested replies
- Explanation feedback (helpful/not helpful)
- Topic-based browsing
- CSV/JSON export
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
- `claude` (default) — Uses Claude API for high-quality explanations
- `ollama` — Uses local Ollama for free development

Embeddings always use OpenAI `text-embedding-3-small` for consistent vector space.

## License

MIT
