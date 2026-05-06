-- Embeddings replaced by Postgres FTS in 20260405045258_add_full_text_search.
-- Drop the now-unused table and its semantic search function.
DROP FUNCTION IF EXISTS match_bills(vector, float, int);
DROP TABLE IF EXISTS embeddings;
