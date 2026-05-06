-- Enable RLS on all tables
ALTER TABLE bills ENABLE ROW LEVEL SECURITY;
ALTER TABLE explanations ENABLE ROW LEVEL SECURITY;
ALTER TABLE embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookmarks ENABLE ROW LEVEL SECURITY;
ALTER TABLE bill_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE comment_upvotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE explanation_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE bill_topics ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingestion_jobs ENABLE ROW LEVEL SECURITY;

-- Bills: public read
CREATE POLICY "Bills are publicly readable" ON bills FOR SELECT USING (true);
CREATE POLICY "Bills are managed by service role" ON bills FOR ALL USING (auth.role() = 'service_role');

-- Explanations: public read
CREATE POLICY "Explanations are publicly readable" ON explanations FOR SELECT USING (true);
CREATE POLICY "Explanations are managed by service role" ON explanations FOR ALL USING (auth.role() = 'service_role');

-- Embeddings: service role only
CREATE POLICY "Embeddings are managed by service role" ON embeddings FOR ALL USING (auth.role() = 'service_role');

-- User profiles: users manage their own
CREATE POLICY "Users can view own profile" ON user_profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON user_profiles FOR UPDATE USING (auth.uid() = id);

-- Bookmarks: users manage their own
CREATE POLICY "Users can view own bookmarks" ON bookmarks FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create own bookmarks" ON bookmarks FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can delete own bookmarks" ON bookmarks FOR DELETE USING (auth.uid() = user_id);

-- Bill tracking: users manage their own
CREATE POLICY "Users can view own tracking" ON bill_tracking FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create own tracking" ON bill_tracking FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own tracking" ON bill_tracking FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own tracking" ON bill_tracking FOR DELETE USING (auth.uid() = user_id);

-- Comments: public read, authenticated write own
CREATE POLICY "Comments are publicly readable" ON comments FOR SELECT USING (true);
CREATE POLICY "Authenticated users can create comments" ON comments FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own comments" ON comments FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own comments" ON comments FOR DELETE USING (auth.uid() = user_id);

-- Comment upvotes: authenticated users manage own
CREATE POLICY "Users can view own upvotes" ON comment_upvotes FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create own upvotes" ON comment_upvotes FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can delete own upvotes" ON comment_upvotes FOR DELETE USING (auth.uid() = user_id);

-- Explanation feedback: anyone can submit, users see own
CREATE POLICY "Anyone can submit feedback" ON explanation_feedback FOR INSERT WITH CHECK (true);
CREATE POLICY "Users can view own feedback" ON explanation_feedback FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);

-- Bill topics: public read
CREATE POLICY "Topics are publicly readable" ON bill_topics FOR SELECT USING (true);
CREATE POLICY "Topics are managed by service role" ON bill_topics FOR ALL USING (auth.role() = 'service_role');

-- Ingestion jobs: service role only
CREATE POLICY "Jobs are managed by service role" ON ingestion_jobs FOR ALL USING (auth.role() = 'service_role');
