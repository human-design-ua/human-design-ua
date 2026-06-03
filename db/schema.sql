-- Human Design Project — Database Schema
-- Version: 1.0
-- Execute in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- TABLE: users
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email             VARCHAR(255) UNIQUE NOT NULL,
  created_at        TIMESTAMPTZ DEFAULT now(),
  plan              VARCHAR(10) CHECK (plan IN ('basic', 'full')),
  status            VARCHAR(20) CHECK (status IN ('pending','paid','delivered','upsold')),
  birth_date        DATE,
  birth_time        TIME,
  birth_place       VARCHAR(255),
  -- Human Design calculated fields
  hd_type           VARCHAR(50),   -- Маніфестор, Генератор, МГ, Проектор, Рефлектор
  hd_authority      VARCHAR(50),   -- Емоційний, Сакральний, Селезінковий, etc.
  hd_profile        VARCHAR(20),   -- 1/3, 2/4, 3/5, etc.
  hd_definition     VARCHAR(20),   -- Single, Split, Triple, Quadruple
  -- Content
  reading_text      TEXT,          -- згенерована розшифровка
  reading_generated_at TIMESTAMPTZ,
  -- Payment
  liqpay_order_id   VARCHAR(100),
  amount_paid       NUMERIC(10,2),
  paid_at           TIMESTAMPTZ,
  -- Upsell
  upsell_sent_at    TIMESTAMPTZ,
  upsell_converted  BOOLEAN DEFAULT false,
  upsell_converted_at TIMESTAMPTZ,
  -- UTM & Analytics
  utm_source        VARCHAR(100),
  utm_medium        VARCHAR(100),
  utm_campaign      VARCHAR(100),
  utm_content       VARCHAR(100),
  -- Meta
  ip_address        INET,
  user_agent        TEXT,
  referrer          TEXT
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_plan ON users(plan);

-- ============================================================
-- TABLE: orders
-- ============================================================
CREATE TABLE IF NOT EXISTS orders (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID REFERENCES users(id) ON DELETE SET NULL,
  created_at        TIMESTAMPTZ DEFAULT now(),
  plan              VARCHAR(10) CHECK (plan IN ('basic', 'full')),
  amount            NUMERIC(10,2) NOT NULL,
  currency          CHAR(3) DEFAULT 'UAH',
  payment_provider  VARCHAR(50) DEFAULT 'liqpay',
  payment_status    VARCHAR(20) CHECK (payment_status IN ('pending','success','failed','refunded')),
  provider_order_id VARCHAR(100),
  provider_payment_id VARCHAR(100),
  -- Delivery
  email_sent_at     TIMESTAMPTZ,
  email_provider    VARCHAR(50)  -- brevo, sendgrid
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_payment_status ON orders(payment_status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_provider_order_id ON orders(provider_order_id);

-- ============================================================
-- TABLE: upsell_events
-- ============================================================
CREATE TABLE IF NOT EXISTS upsell_events (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID REFERENCES users(id) ON DELETE SET NULL,
  created_at    TIMESTAMPTZ DEFAULT now(),
  sent_at       TIMESTAMPTZ,
  opened_at     TIMESTAMPTZ,
  clicked_at    TIMESTAMPTZ,
  converted_at  TIMESTAMPTZ,
  amount        NUMERIC(10,2),
  order_id      UUID REFERENCES orders(id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_upsell_user_id ON upsell_events(user_id);
CREATE INDEX IF NOT EXISTS idx_upsell_sent_at ON upsell_events(sent_at);

-- ============================================================
-- TABLE: error_logs
-- ============================================================
CREATE TABLE IF NOT EXISTS error_logs (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at  TIMESTAMPTZ DEFAULT now(),
  source      VARCHAR(50),   -- make, claude_api, liqpay, brevo, supabase
  error_code  VARCHAR(100),
  error_msg   TEXT,
  context     JSONB,         -- додаткові дані (user_id, order_id, etc.)
  resolved    BOOLEAN DEFAULT false,
  resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_error_logs_source ON error_logs(source);
CREATE INDEX IF NOT EXISTS idx_error_logs_created_at ON error_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_error_logs_resolved ON error_logs(resolved);
