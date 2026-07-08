-- Support tickets submitted via the public POST /tickets endpoint.
-- Idempotent so it is safe to re-run and mirrors db/pool.py bootstrap DDL.
-- Apply to production (which skips the startup bootstrap) with:
--   psql "$SUPABASE_URL" -f db/migrations/006_tickets.sql

CREATE TABLE IF NOT EXISTS tickets (
    id                UUID PRIMARY KEY,
    category          TEXT NOT NULL,
    status            TEXT NOT NULL DEFAULT 'open',
    subject           TEXT NOT NULL,
    description       TEXT NOT NULL,
    recipe_url        TEXT,
    metadata          JSONB NOT NULL DEFAULT '{}',
    submitter_ip_hash TEXT,          -- salted SHA-256 of client IP, never the raw IP
    user_agent        TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets (created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_tickets_category ON tickets (category);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets (status);
