-- Add a generated tsvector column for full-text search
ALTER TABLE bills ADD COLUMN IF NOT EXISTS fts tsvector
  GENERATED ALWAYS AS (
    setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(summary, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(policy_area, '')), 'C')
  ) STORED;

-- GIN index for fast full-text search
CREATE INDEX IF NOT EXISTS idx_bills_fts ON bills USING gin(fts);

-- Full-text search function with ranking
CREATE OR REPLACE FUNCTION search_bills_fts(
  search_query text,
  match_count int DEFAULT 20,
  page_offset int DEFAULT 0
)
RETURNS TABLE (
  bill_id uuid,
  rank real
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    b.id AS bill_id,
    ts_rank(b.fts, websearch_to_tsquery('english', search_query)) AS rank
  FROM bills b
  WHERE b.fts @@ websearch_to_tsquery('english', search_query)
  ORDER BY rank DESC
  LIMIT match_count
  OFFSET page_offset;
END;
$$ LANGUAGE plpgsql;
