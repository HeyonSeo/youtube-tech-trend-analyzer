-- TechPulse Database Schema

-- Analysis runs table
CREATE TABLE IF NOT EXISTS analysis_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_date TIMESTAMPTZ NOT NULL DEFAULT now(),
    region VARCHAR(10) NOT NULL DEFAULT 'all',
    period_days INTEGER NOT NULL DEFAULT 7,
    video_count INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'running',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Keywords table
CREATE TABLE IF NOT EXISTS keywords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    keyword VARCHAR(100) NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    category VARCHAR(50),
    rank INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Videos table
CREATE TABLE IF NOT EXISTS videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    video_id VARCHAR(20) NOT NULL,
    title TEXT NOT NULL,
    channel VARCHAR(200),
    views BIGINT NOT NULL DEFAULT 0,
    likes BIGINT NOT NULL DEFAULT 0,
    published_at TIMESTAMPTZ,
    language VARCHAR(10),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_keywords_run_id ON keywords(run_id);
CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword);
CREATE INDEX IF NOT EXISTS idx_videos_run_id ON videos(run_id);
CREATE INDEX IF NOT EXISTS idx_videos_video_id ON videos(video_id);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_date ON analysis_runs(run_date DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_region ON analysis_runs(region);

-- Enable Row Level Security (optional, for multi-tenant)
ALTER TABLE analysis_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE keywords ENABLE ROW LEVEL SECURITY;
ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
