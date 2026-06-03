-- Migration 001: Initial schema
-- Date: 2026-06-03
-- Run schema.sql and rls-policies.sql
-- This file documents the initial migration

-- Step 1: Run db/schema.sql
-- Step 2: Run db/rls-policies.sql
-- Step 3: Verify with:
--   SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

-- Migration complete marker
SELECT 'Migration 001 complete: users, orders, upsell_events, error_logs created' AS status;
