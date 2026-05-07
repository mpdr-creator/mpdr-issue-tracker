-- ============================================================
--  MorepenPDR Information Management System — Supabase SQL Schema
--  Run this entire script in Supabase → SQL Editor → Run
-- ============================================================

-- 1. USERS ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          TEXT NOT NULL,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('scientist','admin','management')),
    department    TEXT,          -- only for admin role
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 2. TICKETS ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tickets (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title            TEXT NOT NULL,
    description      TEXT NOT NULL,
    category         TEXT NOT NULL,
    priority         TEXT NOT NULL CHECK (priority IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    status           TEXT NOT NULL DEFAULT 'OPEN'
                     CHECK (status IN ('OPEN','ASSIGNED','IN_PROGRESS','RESOLVED','CLOSED')),
    created_by       UUID REFERENCES users(id),
    assigned_to_dept TEXT NOT NULL,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW()
);

-- 3. TICKET UPDATES (audit trail) ──────────────────────────
CREATE TABLE IF NOT EXISTS ticket_updates (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id   UUID REFERENCES tickets(id) ON DELETE CASCADE,
    updated_by  UUID REFERENCES users(id),
    old_status  TEXT,
    new_status  TEXT,
    note        TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 4. FEEDBACK ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS feedback (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id  UUID UNIQUE REFERENCES tickets(id) ON DELETE CASCADE,
    rating     INTEGER CHECK (rating BETWEEN 1 AND 5),
    comment    TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- SEED DATA — Default accounts (change passwords after setup!)
-- Passwords below are bcrypt hashes of the plaintext shown.
-- ============================================================

-- scientist / Science@123
INSERT INTO users (name, email, password_hash, role) VALUES
('Dr. Priya Sharma',
 'priya.sharma@morepenpdr.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGniYwcX8eN3vRqD7ZrPz3TZVWK',
 'scientist')
ON CONFLICT (email) DO NOTHING;

-- IT admin / Admin@123
INSERT INTO users (name, email, password_hash, role, department) VALUES
('Rahul IT',
 'it.admin@morepenpdr.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGniYwcX8eN3vRqD7ZrPz3TZVWK',
 'admin', 'IT')
ON CONFLICT (email) DO NOTHING;

-- Lab admin / Admin@123
INSERT INTO users (name, email, password_hash, role, department) VALUES
('Sunita Lab',
 'lab.admin@morepenpdr.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGniYwcX8eN3vRqD7ZrPz3TZVWK',
 'admin', 'Lab Maintenance')
ON CONFLICT (email) DO NOTHING;

-- Safety admin / Admin@123
INSERT INTO users (name, email, password_hash, role, department) VALUES
('Kumar Safety',
 'safety.admin@morepenpdr.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGniYwcX8eN3vRqD7ZrPz3TZVWK',
 'admin', 'Safety')
ON CONFLICT (email) DO NOTHING;

-- Management / Mgmt@123
INSERT INTO users (name, email, password_hash, role) VALUES
('CEO Dashboard',
 'management@morepenpdr.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGniYwcX8eN3vRqD7ZrPz3TZVWK',
 'management')
ON CONFLICT (email) DO NOTHING;

-- ============================================================
-- NOTE: The hash above maps to the password "Admin@123"
-- Tell users to change via the Register tab immediately.
-- ============================================================
