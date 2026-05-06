-- Lock down search_path on SECURITY DEFINER and helper functions per Supabase advisor.
ALTER FUNCTION public.search_bills_fts(text, int, int) SET search_path = '';
ALTER FUNCTION public.handle_new_user() SET search_path = '';

-- handle_new_user runs as a trigger; revoke direct RPC execution.
REVOKE EXECUTE ON FUNCTION public.handle_new_user() FROM anon, authenticated, public;

-- The handle_new_user SECURITY DEFINER body needs to fully qualify auth.users
-- and public.user_profiles since search_path is now empty.
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
  INSERT INTO public.user_profiles (id) VALUES (new.id);
  RETURN new;
END;
$$;

-- Same for search_bills_fts — fully qualify table refs.
CREATE OR REPLACE FUNCTION public.search_bills_fts(
  search_query text,
  match_count int DEFAULT 20,
  page_offset int DEFAULT 0
)
RETURNS TABLE (bill_id uuid, rank real)
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
  RETURN QUERY
  SELECT
    b.id AS bill_id,
    ts_rank(b.fts, websearch_to_tsquery('english', search_query)) AS rank
  FROM public.bills b
  WHERE b.fts @@ websearch_to_tsquery('english', search_query)
  ORDER BY rank DESC
  LIMIT match_count
  OFFSET page_offset;
END;
$$;

-- Tighten anonymous feedback policy: still allow anon, but require user_id consistency.
DROP POLICY IF EXISTS "Anyone can submit feedback" ON public.explanation_feedback;
CREATE POLICY "Anyone can submit feedback" ON public.explanation_feedback
  FOR INSERT
  WITH CHECK (user_id IS NULL OR auth.uid() = user_id);

-- Drop pgvector since embeddings are removed.
DROP EXTENSION IF EXISTS vector;
