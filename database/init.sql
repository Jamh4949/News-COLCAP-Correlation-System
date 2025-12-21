-- Database initialization script for News-COLCAP System

-- Create news table
CREATE TABLE IF NOT EXISTS news (
    id SERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    source TEXT,
    published_date TIMESTAMP NOT NULL,
    country VARCHAR(10),
    sentiment_score FLOAT,
    sentiment_label VARCHAR(20),
    categories TEXT[],
    keywords TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create COLCAP index data table
CREATE TABLE IF NOT EXISTS colcap_data (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    open_price DECIMAL(10, 2),
    high_price DECIMAL(10, 2),
    low_price DECIMAL(10, 2),
    close_price DECIMAL(10, 2),
    volume BIGINT,
    adj_close DECIMAL(10, 2),
    daily_change DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create correlations table
CREATE TABLE IF NOT EXISTS correlations (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    news_count INTEGER,
    avg_sentiment FLOAT,
    colcap_change DECIMAL(10, 4),
    correlation_coefficient FLOAT,
    news_ids INTEGER[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create processing queue status table
CREATE TABLE IF NOT EXISTS processing_status (
    id SERIAL PRIMARY KEY,
    job_id UUID UNIQUE NOT NULL,
    service_name VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB
);

-- Create indexes for performance
CREATE INDEX idx_news_published_date ON news(published_date DESC);
CREATE INDEX idx_news_country ON news(country);
CREATE INDEX idx_news_sentiment ON news(sentiment_score);
CREATE INDEX idx_colcap_date ON colcap_data(date DESC);
CREATE INDEX idx_correlations_date ON correlations(date DESC);
CREATE INDEX idx_processing_status ON processing_status(status, service_name);

-- Create view for daily summary
CREATE OR REPLACE VIEW daily_news_summary AS
SELECT 
    DATE(published_date) as date,
    COUNT(*) as news_count,
    AVG(sentiment_score) as avg_sentiment,
    COUNT(CASE WHEN sentiment_label = 'positive' THEN 1 END) as positive_count,
    COUNT(CASE WHEN sentiment_label = 'negative' THEN 1 END) as negative_count,
    COUNT(CASE WHEN sentiment_label = 'neutral' THEN 1 END) as neutral_count
FROM news
GROUP BY DATE(published_date)
ORDER BY date DESC;

-- Create function to update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for news table
CREATE TRIGGER update_news_updated_at BEFORE UPDATE ON news
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample COLCAP data (for testing)
INSERT INTO colcap_data (date, open_price, high_price, low_price, close_price, volume, adj_close, daily_change)
VALUES 
    (CURRENT_DATE - INTERVAL '1 day', 1650.50, 1670.20, 1645.30, 1665.80, 1500000, 1665.80, 0.92),
    (CURRENT_DATE - INTERVAL '2 days', 1635.20, 1655.40, 1630.10, 1650.50, 1450000, 1650.50, 0.94)
ON CONFLICT (date) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO newsuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO newsuser;
