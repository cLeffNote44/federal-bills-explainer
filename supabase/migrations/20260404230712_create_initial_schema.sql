-- Bills table
CREATE TABLE bills (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  congress integer NOT NULL,
  bill_type text NOT NULL,
  number integer NOT NULL,
  title text NOT NULL,
  summary text,
  status text NOT NULL DEFAULT 'introduced',
  introduced_date date,
  latest_action_date timestamptz,
  latest_action_text text,
  congress_url text,
  public_law_number text,
  sponsor jsonb,
  cosponsors_count integer,
  committees jsonb,
  subjects jsonb,
  policy_area text,
  text_url text,
  version integer NOT NULL DEFAULT 1,
  checksum text,
  last_fetched_at timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_bill_identity UNIQUE (congress, bill_type, number)
);

CREATE INDEX idx_bills_latest_action ON bills (latest_action_date);
CREATE INDEX idx_bills_status ON bills (status);
CREATE INDEX idx_bills_public_law ON bills (public_law_number);
CREATE INDEX idx_bills_congress_type_number ON bills (congress, bill_type, number);

-- Explanations table
CREATE TABLE explanations (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  bill_id uuid NOT NULL REFERENCES bills(id) ON DELETE CASCADE,
  text text NOT NULL,
  simple_text text,
  model_name text NOT NULL,
  model_provider text NOT NULL,
  version integer NOT NULL DEFAULT 1,
  generated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_explanations_bill ON explanations (bill_id);

-- Embeddings table (pgvector) — superseded by FTS in 20260506_drop_embeddings
CREATE TABLE embeddings (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  bill_id uuid NOT NULL REFERENCES bills(id) ON DELETE CASCADE,
  vector vector(1536) NOT NULL,
  model_name text NOT NULL,
  content_hash text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_embedding_cache UNIQUE (content_hash, model_name)
);

CREATE INDEX idx_embeddings_vector ON embeddings USING hnsw (vector vector_cosine_ops);

-- User profiles (extends auth.users)
CREATE TABLE user_profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name text,
  zip_code text,
  state text,
  email_notifications boolean NOT NULL DEFAULT true,
  notification_frequency text NOT NULL DEFAULT 'daily',
  preferences jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Bookmarks
CREATE TABLE bookmarks (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  bill_id uuid NOT NULL REFERENCES bills(id) ON DELETE CASCADE,
  notes text,
  folder text,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_user_bill_bookmark UNIQUE (user_id, bill_id)
);

CREATE INDEX idx_bookmarks_user ON bookmarks (user_id);

-- Bill tracking
CREATE TABLE bill_tracking (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  bill_id uuid NOT NULL REFERENCES bills(id) ON DELETE CASCADE,
  notify_on_status_change boolean NOT NULL DEFAULT true,
  notify_on_vote boolean NOT NULL DEFAULT true,
  email_notifications boolean NOT NULL DEFAULT false,
  last_known_status text,
  last_notified_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_user_bill_tracking UNIQUE (user_id, bill_id)
);

CREATE INDEX idx_tracking_user ON bill_tracking (user_id);

-- Comments
CREATE TABLE comments (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  bill_id uuid NOT NULL REFERENCES bills(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  parent_id uuid REFERENCES comments(id) ON DELETE CASCADE,
  content text NOT NULL,
  is_deleted boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_comments_bill ON comments (bill_id);
CREATE INDEX idx_comments_user ON comments (user_id);

-- Comment upvotes (composite PK)
CREATE TABLE comment_upvotes (
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  comment_id uuid NOT NULL REFERENCES comments(id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, comment_id)
);

-- Explanation feedback
CREATE TABLE explanation_feedback (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  explanation_id uuid NOT NULL REFERENCES explanations(id) ON DELETE CASCADE,
  user_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  session_id text,
  is_helpful boolean NOT NULL,
  feedback_text text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_feedback_explanation ON explanation_feedback (explanation_id);

-- Bill topics
CREATE TABLE bill_topics (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  bill_id uuid NOT NULL REFERENCES bills(id) ON DELETE CASCADE,
  topic_name text NOT NULL,
  confidence_score real,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_bill_topic UNIQUE (bill_id, topic_name)
);

CREATE INDEX idx_topics_name ON bill_topics (topic_name);

-- Ingestion jobs
CREATE TABLE ingestion_jobs (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  job_type text NOT NULL,
  status text NOT NULL DEFAULT 'pending',
  config jsonb,
  total_records integer NOT NULL DEFAULT 0,
  processed_records integer NOT NULL DEFAULT 0,
  failed_records integer NOT NULL DEFAULT 0,
  error_message text,
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_jobs_status ON ingestion_jobs (status);
CREATE INDEX idx_jobs_created ON ingestion_jobs (created_at);

-- Auto-create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.user_profiles (id)
  VALUES (new.id);
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Semantic search function (superseded by search_bills_fts in 20260405045258)
CREATE OR REPLACE FUNCTION match_bills(
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.5,
  match_count int DEFAULT 20
)
RETURNS TABLE (
  bill_id uuid,
  similarity float
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    e.bill_id,
    1 - (e.vector <=> query_embedding) AS similarity
  FROM embeddings e
  WHERE 1 - (e.vector <=> query_embedding) > match_threshold
  ORDER BY e.vector <=> query_embedding
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;
