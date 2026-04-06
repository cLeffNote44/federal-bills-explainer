import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as schema from "./schema";

function createDb() {
  const connectionString = process.env.DATABASE_URL;
  if (!connectionString) {
    throw new Error(
      "DATABASE_URL is not set. Add it to your environment variables."
    );
  }
  return drizzle(
    postgres(connectionString, { prepare: false, max: 1 }),
    { schema }
  );
}

// Lazy singleton — only connects when first accessed
let _db: ReturnType<typeof createDb> | null = null;

export function getDb() {
  if (!_db) _db = createDb();
  return _db;
}

// Convenience export for existing imports — uses getter under the hood
export const db = new Proxy({} as ReturnType<typeof createDb>, {
  get(_target, prop) {
    return (getDb() as unknown as Record<string | symbol, unknown>)[prop];
  },
});

export type Database = ReturnType<typeof createDb>;
