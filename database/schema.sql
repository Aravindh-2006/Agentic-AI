-- Database Schema for AI Startup Validation Agent

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT,
    google_id TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS validation_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    idea_title TEXT NOT NULL,
    idea_description TEXT NOT NULL,
    status TEXT NOT NULL, -- 'pending', 'market_research', 'competitor_analysis', 'customer_persona', 'revenue_model', 'swot_analysis', 'scoring', 'report_generation', 'completed', 'failed'
    error_message TEXT,
    market_research TEXT,
    competitor_analysis TEXT,
    customer_persona TEXT,
    revenue_model TEXT,
    swot_analysis TEXT,
    feasibility_scores TEXT, -- JSON string
    overall_score REAL DEFAULT 0.0,
    final_report TEXT,
    pdf_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- AI Startup Mentor chat history
CREATE TABLE IF NOT EXISTS mentor_chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    role TEXT NOT NULL,              -- 'user' | 'assistant'
    content TEXT NOT NULL,           -- plain text message
    structured_response TEXT,        -- JSON string for assistant messages
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(report_id) REFERENCES validation_reports(id) ON DELETE CASCADE
);

-- Startup Roadmap
CREATE TABLE IF NOT EXISTS startup_roadmaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    roadmap_data TEXT NOT NULL,      -- full roadmap JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(report_id) REFERENCES validation_reports(id) ON DELETE CASCADE
);

-- Roadmap Task Progress
CREATE TABLE IF NOT EXISTS roadmap_task_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roadmap_id INTEGER NOT NULL,
    task_key TEXT NOT NULL,          -- e.g. "month_1_task_0"
    completed INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(roadmap_id, task_key),
    FOREIGN KEY(roadmap_id) REFERENCES startup_roadmaps(id) ON DELETE CASCADE
);
