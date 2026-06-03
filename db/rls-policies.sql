-- Human Design Project — Row Level Security Policies
-- Execute AFTER schema.sql

-- ============================================================
-- TABLE: users
-- ============================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Анонімний користувач може тільки вставляти нові записи (через фронтенд)
CREATE POLICY "anon_can_insert_users"
  ON users FOR INSERT
  TO anon
  WITH CHECK (true);

-- Авторизований користувач бачить тільки свої дані
CREATE POLICY "user_can_view_own"
  ON users FOR SELECT
  TO authenticated
  USING (auth.uid() = id);

-- Service Role може все (Make.com)
CREATE POLICY "service_role_full_access_users"
  ON users FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- ============================================================
-- TABLE: orders
-- ============================================================
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_full_access_orders"
  ON orders FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY "user_can_view_own_orders"
  ON orders FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

-- ============================================================
-- TABLE: upsell_events
-- ============================================================
ALTER TABLE upsell_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_full_access_upsell"
  ON upsell_events FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- ============================================================
-- TABLE: error_logs
-- ============================================================
ALTER TABLE error_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_full_access_errors"
  ON error_logs FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);
