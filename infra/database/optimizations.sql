-- Database Performance Optimizations for Federal Bills Explainer
-- Run this after initial setup to add indexes and optimize queries

-- ====================
-- INDEXES FOR BILLS TABLE
-- ====================

-- Index for searching by status (frequently filtered)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bills_status
ON bills(status) WHERE status IS NOT NULL;

-- Index for searching by date (chronological queries)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bills_introduced_date
ON bills(introduced_date DESC) WHERE introduced_date IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bills_latest_action_date
ON bills(latest_action_date DESC) WHERE latest_action_date IS NOT NULL;

-- Composite index for common queries (congress + bill_type + number)
-- This is likely already enforced by PRIMARY KEY or UNIQUE constraint
-- CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_bills_identity
-- ON bills(congress, bill_type, number);

-- Index for public law searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bills_public_law
ON bills(public_law_number) WHERE public_law_number IS NOT NULL;

-- Full-text search index on title
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bills_title_fts
ON bills USING gin(to_tsvector('english', title));

-- Full-text search index on summary
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bills_summary_fts
ON bills USING gin(to_tsvector('english', summary)) WHERE summary IS NOT NULL;

-- JSONB indexes for committees and subjects (if stored as JSONB)
-- Uncomment if using JSONB columns
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bills_committees_gin
-- ON bills USING gin(committees);
--
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bills_subjects_gin
-- ON bills USING gin(subjects);

-- ====================
-- INDEXES FOR EXPLANATIONS TABLE
-- ====================

-- Index for foreign key relationship
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_explanations_bill_id
ON explanations(bill_id);

-- Index for model name (useful for filtering by explanation model)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_explanations_model_name
ON explanations(model_name);

-- Index for version (to quickly get latest explanation)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_explanations_version
ON explanations(bill_id, version DESC);

-- Index for created_at timestamp
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_explanations_created_at
ON explanations(created_at DESC);

-- ====================
-- INDEXES FOR EMBEDDINGS TABLE
-- ====================

-- Index for foreign key relationship
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_embeddings_bill_id
ON embeddings(bill_id);

-- Index for content hash (deduplication)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_embeddings_content_hash
ON embeddings(content_hash);

-- Index for model name
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_embeddings_model_name
ON embeddings(model_name);

-- IVFFlat index for vector similarity search (pgvector)
-- Adjust lists parameter based on your data size (rule of thumb: rows / 1000)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_embeddings_vector_ivfflat
ON embeddings USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);

-- Alternative: HNSW index (faster queries, slower builds)
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_embeddings_vector_hnsw
-- ON embeddings USING hnsw (vector vector_cosine_ops);

-- ====================
-- INDEXES FOR INGESTION STATE
-- ====================

-- Small table, probably doesn't need indexes
-- Single-row table for tracking ingestion state

-- ====================
-- STATISTICS UPDATES
-- ====================

-- Update table statistics for better query planning
ANALYZE bills;
ANALYZE explanations;
ANALYZE embeddings;
ANALYZE ingestion_state;

-- ====================
-- QUERY OPTIMIZATION SETTINGS
-- ====================

-- Increase statistics target for frequently queried columns
ALTER TABLE bills ALTER COLUMN status SET STATISTICS 1000;
ALTER TABLE bills ALTER COLUMN introduced_date SET STATISTICS 1000;
ALTER TABLE bills ALTER COLUMN title SET STATISTICS 500;

-- ====================
-- VACUUM AND MAINTENANCE
-- ====================

-- Vacuum tables to reclaim space and update statistics
VACUUM ANALYZE bills;
VACUUM ANALYZE explanations;
VACUUM ANALYZE embeddings;

-- ====================
-- PERFORMANCE MONITORING QUERIES
-- ====================

-- Check index usage
-- SELECT
--     schemaname,
--     tablename,
--     indexname,
--     idx_scan,
--     idx_tup_read,
--     idx_tup_fetch
-- FROM pg_stat_user_indexes
-- WHERE schemaname = 'public'
-- ORDER BY idx_scan DESC;

-- Check table sizes
-- SELECT
--     tablename,
--     pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
--     pg_total_relation_size(schemaname||'.'||tablename) AS bytes
-- FROM pg_tables
-- WHERE schemaname = 'public'
-- ORDER BY bytes DESC;

-- Check slow queries (requires pg_stat_statements extension)
-- SELECT
--     query,
--     calls,
--     total_exec_time,
--     mean_exec_time,
--     max_exec_time
-- FROM pg_stat_statements
-- ORDER BY mean_exec_time DESC
-- LIMIT 20;

-- ====================
-- MAINTENANCE RECOMMENDATIONS
-- ====================

-- 1. Run VACUUM ANALYZE weekly or after bulk inserts
-- 2. Monitor index bloat and reindex if necessary
-- 3. Adjust pgvector index parameters as data grows
-- 4. Review slow query log regularly
-- 5. Update statistics after significant data changes

-- ====================
-- CONNECTION POOLING
-- ====================

-- Recommended PgBouncer settings (add to pgbouncer.ini)
-- [databases]
-- federal_bills = host=localhost port=5432 dbname=federal_bills
--
-- [pgbouncer]
-- pool_mode = transaction
-- max_client_conn = 1000
-- default_pool_size = 25
-- min_pool_size = 5
-- reserve_pool_size = 5
-- reserve_pool_timeout = 3
-- max_db_connections = 50
-- max_user_connections = 50
