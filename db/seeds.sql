-- Human Design Project — Test Seed Data
-- Use ONLY in development/staging environment

-- Test user (basic plan)
INSERT INTO users (
  id, email, plan, status,
  birth_date, birth_time, birth_place,
  hd_type, hd_authority, hd_profile,
  liqpay_order_id, amount_paid, paid_at,
  utm_source, utm_campaign
) VALUES (
  'a1b2c3d4-0000-0000-0000-000000000001',
  'test.basic@example.com',
  'basic', 'delivered',
  '1990-05-15', '14:30', 'Київ, Україна',
  'Генератор', 'Сакральний', '2/4',
  'TEST-ORDER-001', 399.00, now() - interval '2 hours',
  'meta', 'hd_ukraine_test'
);

-- Test order for basic user
INSERT INTO orders (
  user_id, plan, amount, payment_status,
  provider_order_id, email_sent_at
) VALUES (
  'a1b2c3d4-0000-0000-0000-000000000001',
  'basic', 399.00, 'success',
  'TEST-ORDER-001', now() - interval '1 hour 50 minutes'
);

-- Test user (full plan)
INSERT INTO users (
  id, email, plan, status,
  birth_date, birth_time, birth_place,
  hd_type, hd_authority, hd_profile,
  liqpay_order_id, amount_paid, paid_at
) VALUES (
  'a1b2c3d4-0000-0000-0000-000000000002',
  'test.full@example.com',
  'full', 'delivered',
  '1985-11-22', '08:00', 'Львів, Україна',
  'Проектор', 'Селезінковий', '3/5',
  'TEST-ORDER-002', 799.00, now() - interval '5 hours'
);

-- Cleanup test data (run when done):
-- DELETE FROM orders WHERE provider_order_id LIKE 'TEST-%';
-- DELETE FROM users WHERE email LIKE '%@example.com';
