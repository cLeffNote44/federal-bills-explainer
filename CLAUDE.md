# CLAUDE.md — Federal Bills Explainer

## Project Overview
AI-powered platform that makes federal legislation accessible through plain-language explanations and semantic search. Built with Next.js 15, Supabase, and the Vercel AI SDK.

## Tech Stack
- **Framework**: Next.js 15 (App Router), TypeScript strict
- **Database**: Supabase (Postgres + pgvector + Auth + RLS)
- **ORM**: Drizzle ORM
- **AI**: Claude API (prod) + Ollama (local dev) via Vercel AI SDK
- **Search**: Postgres full-text search (weighted tsvector on title/summary/policy_area)
- **Styling**: Tailwind CSS 4 + shadcn/ui
- **State**: Zustand + TanStack React Query
- **Deployment**: Vercel + Supabase

## Key Conventions
- Server Components by default; `"use client"` only when needed
- Zod validation at all API boundaries (`src/lib/validators.ts`)
- Drizzle schema is the source of truth (`src/lib/db/schema.ts`)
- Named exports only
- `AI_PROVIDER` env var switches between Claude and Ollama

## Directory Structure
- `src/app/` — Pages and API routes
- `src/components/` — UI components organized by domain
- `src/lib/` — Business logic (db, ai, congress, ingestion, supabase, validators)
- `src/hooks/` — TanStack Query hooks
- `src/stores/` — Zustand stores
- `src/types/` — Shared TypeScript types
- `supabase/migrations/` — Database migrations

## Supabase Project
- **ID**: ssywdysiszwhpkzohpua
- **Region**: us-east-1
- **URL**: https://ssywdysiszwhpkzohpua.supabase.co

## Commands
- `pnpm dev` — Start dev server
- `pnpm build` — Production build
- `pnpm lint` — ESLint
- `pnpm db:generate` — Generate Drizzle migration
- `pnpm db:push` — Push schema to DB
