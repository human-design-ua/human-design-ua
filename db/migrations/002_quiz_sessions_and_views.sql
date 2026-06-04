-- Migration 002: Quiz sessions + analytics views
-- Date: 2026-06-04
-- Run in Supabase SQL Editor AFTER 001_init.sql

-- ============================================================
-- TABLE: quiz_sessions
-- Зберігає всі розпочаті квізи (навіть без оплати)
-- Потрібно для: ретаргетингу, аналізу dropout, email-відновлення
-- ============================================================
CREATE TABLE IF NOT EXISTS quiz_sessions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now(),
  -- Дані з квізу
  name            VARCHAR(100),
  email           VARCHAR(255),
  birth_date      DATE,
  birth_time      TIME,
  birth_place     VARCHAR(255),
  life_area       VARCHAR(50),   -- career, relationships, energy, self
  challenge       VARCHAR(50),   -- decisions, fatigue, purpose, people
  -- Прогрес
  step_reached    INTEGER DEFAULT 1,  -- до якого кроку дійшли
  plan_selected   VARCHAR(10),        -- basic | full | null (не вибрали)
  -- Конверсія
  converted       BOOLEAN DEFAULT false,
  order_id        UUID REFERENCES orders(id),
  -- UTM
  utm_source      VARCHAR(100),
  utm_medium      VARCHAR(100),
  utm_campaign    VARCHAR(100),
  utm_content     VARCHAR(100),
  -- Meta
  ip_address      INET,
  user_agent      TEXT,
  referrer        TEXT,
  session_id      VARCHAR(100)  -- з localStorage/cookie
);

CREATE INDEX IF NOT EXISTS idx_quiz_sessions_email     ON quiz_sessions(email);
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_converted ON quiz_sessions(converted);
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_created   ON quiz_sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_utm       ON quiz_sessions(utm_source, utm_campaign);

-- RLS для quiz_sessions
ALTER TABLE quiz_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_can_insert_quiz_sessions"
  ON quiz_sessions FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "anon_can_update_own_session"
  ON quiz_sessions FOR UPDATE TO anon
  USING (session_id = current_setting('app.session_id', true));

CREATE POLICY "service_role_full_access_quiz"
  ON quiz_sessions FOR ALL TO service_role
  USING (true) WITH CHECK (true);

-- ============================================================
-- VIEW: v_orders_dashboard
-- Зручний дашборд для відстеження замовлень
-- ============================================================
CREATE OR REPLACE VIEW v_orders_dashboard AS
SELECT
  u.id,
  u.email,
  u.created_at,
  u.plan,
  u.status,
  u.hd_type,
  u.hd_profile,
  u.birth_place,
  u.amount_paid,
  u.paid_at,
  u.reading_generated_at,
  o.email_sent_at,
  u.upsell_converted,
  u.utm_source,
  u.utm_campaign,
  EXTRACT(EPOCH FROM (o.email_sent_at - u.paid_at))/60 AS delivery_minutes
FROM users u
LEFT JOIN orders o ON o.user_id = u.id AND o.payment_status = 'success'
ORDER BY u.created_at DESC;

-- ============================================================
-- VIEW: v_daily_stats
-- Щоденна статистика для відстеження KPI
-- ============================================================
CREATE OR REPLACE VIEW v_daily_stats AS
SELECT
  DATE(created_at)                          AS day,
  COUNT(*)                                  AS total_orders,
  COUNT(*) FILTER (WHERE plan = 'basic')    AS basic_orders,
  COUNT(*) FILTER (WHERE plan = 'full')     AS full_orders,
  SUM(amount_paid)                          AS revenue_uah,
  AVG(amount_paid)                          AS avg_order,
  COUNT(*) FILTER (WHERE upsell_converted)  AS upsell_converted,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE upsell_converted) /
    NULLIF(COUNT(*) FILTER (WHERE plan = 'basic'), 0), 1
  )                                         AS upsell_rate_pct
FROM users
WHERE status IN ('paid', 'delivered', 'upsold')
GROUP BY DATE(created_at)
ORDER BY day DESC;

-- ============================================================
-- VIEW: v_funnel_stats
-- Аналіз воронки: квіз → вибір тарифу → оплата
-- ============================================================
CREATE OR REPLACE VIEW v_funnel_stats AS
SELECT
  DATE(created_at)                            AS day,
  COUNT(*)                                    AS started_quiz,
  COUNT(*) FILTER (WHERE step_reached >= 3)   AS entered_birth_data,
  COUNT(*) FILTER (WHERE step_reached >= 7)   AS completed_quiz,
  COUNT(*) FILTER (WHERE plan_selected IS NOT NULL) AS selected_plan,
  COUNT(*) FILTER (WHERE converted = true)    AS paid,
  ROUND(100.0 * COUNT(*) FILTER (WHERE converted) / NULLIF(COUNT(*), 0), 1) AS conversion_pct
FROM quiz_sessions
GROUP BY DATE(created_at)
ORDER BY day DESC;

-- ============================================================
-- FUNCTION: get_revenue_summary
-- Підсумок по доходу за період
-- ============================================================
CREATE OR REPLACE FUNCTION get_revenue_summary(
  start_date DATE DEFAULT CURRENT_DATE - INTERVAL '30 days',
  end_date   DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
  period       TEXT,
  orders_count BIGINT,
  revenue_uah  NUMERIC,
  basic_count  BIGINT,
  full_count   BIGINT,
  upsell_count BIGINT
) LANGUAGE sql STABLE AS $$
  SELECT
    start_date::TEXT || ' — ' || end_date::TEXT,
    COUNT(*),
    COALESCE(SUM(amount_paid), 0),
    COUNT(*) FILTER (WHERE plan = 'basic'),
    COUNT(*) FILTER (WHERE plan = 'full'),
    COUNT(*) FILTER (WHERE upsell_converted = true)
  FROM users
  WHERE status IN ('paid','delivered','upsold')
    AND DATE(paid_at) BETWEEN start_date AND end_date;
$$;

-- Migration complete
SELECT 'Migration 002 complete: quiz_sessions, views, functions created' AS status;
