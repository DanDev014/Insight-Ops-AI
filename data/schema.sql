CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    industry VARCHAR(100),
    contract_value NUMERIC(12, 2),
    payment_terms INT, -- e.g., 30 for Net-30
    historical_payment_delay INT, -- average days late
    engagement_score NUMERIC(3, 2) -- scale 0.0 to 1.0
);

CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    client_id INT REFERENCES clients(id),
    name VARCHAR(100) NOT NULL,
    budget NUMERIC(12, 2),
    hours_estimated NUMERIC(8, 2),
    hours_logged NUMERIC(8, 2),
    deadline DATE,
    status VARCHAR(50), -- 'active', 'completed'
    margin NUMERIC(5, 2) -- percentage margin
);

CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    client_id INT REFERENCES clients(id),
    invoice_date DATE,
    due_date DATE,
    paid_date DATE, -- NULL if unpaid
    amount NUMERIC(12, 2)
);

CREATE TABLE IF NOT EXISTS team (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(100),
    hourly_rate NUMERIC(8, 2),
    capacity INT, -- hours per week
    skills TEXT[] -- array of skills
);

CREATE TABLE IF NOT EXISTS time_logs (
    id SERIAL PRIMARY KEY,
    team_member_id INT REFERENCES team(id),
    project_id INT REFERENCES projects(id),
    log_date DATE,
    hours_logged NUMERIC(4, 2),
    task_status VARCHAR(50) -- 'completed', 'in_progress'
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);