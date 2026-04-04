import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as schema from "./schema";

const connectionString = process.env.DATABASE_URL!;

// Use connection pooling for serverless — single connection per request
const client = postgres(connectionString, {
  prepare: false, // Required for Supabase connection pooler (Transaction mode)
  max: 1,
});

export const db = drizzle(client, { schema });

export type Database = typeof db;
