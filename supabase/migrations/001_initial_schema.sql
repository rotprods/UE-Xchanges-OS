-- Chronos Quantum — Supabase Schema
-- Run this in your Supabase SQL Editor to create all tables.

-- ═════════════════════════════════════════════════════════════════════════════
-- 1. Market Snapshots — Complete market state captured every 5 minutes
-- ═════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS market_snapshots (
  id BIGSERIAL PRIMARY KEY,
  timestamp BIGINT NOT NULL,
  symbol VARCHAR(20) NOT NULL,
  price REAL NOT NULL,
  open REAL,
  high REAL,
  low REAL,
  volume_24h REAL,
  -- Technical Indicators
  rsi_14 REAL,
  sma_7 REAL,
  sma_25 REAL,
  sma_99 REAL,
  ema_21 REAL,
  macd_line REAL,
  macd_signal REAL,
  macd_histogram REAL,
  bb_upper REAL,
  bb_lower REAL,
  bb_width REAL,
  vwap REAL,
  adx REAL,
  obv REAL,
  atr_14 REAL,
  -- Trend
  trend_direction VARCHAR(20),
  trend_strength REAL,
  -- On-chain
  btc_mempool_fee REAL,
  eth_gas_gwei REAL,
  whale_count_1h INTEGER,
  liquidation_volume_1h REAL,
  -- Derivatives
  funding_rate REAL,
  open_interest REAL,
  long_short_ratio REAL,
  put_call_ratio REAL,
  -- Sentiment
  fear_greed_index INTEGER,
  -- Macro
  defi_tvl REAL,
  btc_dominance REAL,
  -- Graph Engine Output
  graph_signal_score REAL,
  graph_confidence REAL,
  graph_direction VARCHAR(20),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_snapshots_symbol_ts ON market_snapshots(symbol, timestamp DESC);
CREATE INDEX idx_snapshots_ts ON market_snapshots(timestamp DESC);

-- ═════════════════════════════════════════════════════════════════════════════
-- 2. AI Decisions — Every decision made by the autonomous trader
-- ═════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS ai_decisions (
  id BIGSERIAL PRIMARY KEY,
  timestamp BIGINT NOT NULL,
  wallet_id INTEGER NOT NULL,
  symbol VARCHAR(20) NOT NULL,
  action VARCHAR(10) NOT NULL, -- BUY, SELL, HOLD
  signal_score REAL NOT NULL,
  confidence REAL NOT NULL,
  reasoning TEXT,
  top_signals JSONB DEFAULT '[]',
  snapshot_id BIGINT REFERENCES market_snapshots(id),
  trade_id BIGINT,
  result_pnl REAL,
  was_correct BOOLEAN,
  evaluated_at BIGINT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_decisions_wallet_ts ON ai_decisions(wallet_id, timestamp DESC);
CREATE INDEX idx_decisions_symbol ON ai_decisions(symbol);

-- ═════════════════════════════════════════════════════════════════════════════
-- 3. Paper Wallets — Virtual wallets for strategy testing
-- ═════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS paper_wallets (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  strategy_id VARCHAR(50) NOT NULL,
  initial_capital REAL DEFAULT 100000,
  current_capital REAL DEFAULT 100000,
  assets JSONB DEFAULT '{}',
  avg_cost JSONB DEFAULT '{}',
  total_trades INTEGER DEFAULT 0,
  win_count INTEGER DEFAULT 0,
  loss_count INTEGER DEFAULT 0,
  win_rate REAL DEFAULT 0,
  sharpe_ratio REAL DEFAULT 0,
  max_drawdown REAL DEFAULT 0,
  total_return REAL DEFAULT 0,
  profit_factor REAL DEFAULT 0,
  consecutive_losses INTEGER DEFAULT 0,
  max_consecutive_losses INTEGER DEFAULT 0,
  equity_curve JSONB DEFAULT '[]',
  status VARCHAR(20) DEFAULT 'training',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- ═════════════════════════════════════════════════════════════════════════════
-- 4. Trades — Individual paper/real trades
-- ═════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS trades (
  id BIGSERIAL PRIMARY KEY,
  user_id INTEGER DEFAULT 1,
  wallet_id INTEGER REFERENCES paper_wallets(id),
  symbol VARCHAR(20) NOT NULL,
  side VARCHAR(4) NOT NULL, -- BUY, SELL
  quantity REAL NOT NULL,
  price REAL NOT NULL,
  pnl REAL,
  signal_score REAL,
  confidence REAL,
  reasoning TEXT,
  timestamp BIGINT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_trades_wallet ON trades(wallet_id, timestamp DESC);
CREATE INDEX idx_trades_symbol ON trades(symbol);

-- ═════════════════════════════════════════════════════════════════════════════
-- 5. Strategies — Trading strategy definitions with parameters
-- ═════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS strategies (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  type VARCHAR(50) NOT NULL, -- sma_crossover, rsi_reversion, ensemble_graph, etc.
  parameters JSONB DEFAULT '{}',
  node_weights JSONB DEFAULT '{}',
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- ═════════════════════════════════════════════════════════════════════════════
-- 6. Training Episodes — Results from each AI training cycle
-- ═════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS training_episodes (
  id BIGSERIAL PRIMARY KEY,
  wallet_id INTEGER REFERENCES paper_wallets(id),
  strategy_id INTEGER REFERENCES strategies(id),
  start_ts BIGINT NOT NULL,
  end_ts BIGINT NOT NULL,
  trades_count INTEGER DEFAULT 0,
  total_return REAL DEFAULT 0,
  sharpe_ratio REAL DEFAULT 0,
  win_rate REAL DEFAULT 0,
  max_drawdown REAL DEFAULT 0,
  lessons_learned JSONB DEFAULT '[]',
  weight_adjustments JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_episodes_wallet ON training_episodes(wallet_id);

-- ═════════════════════════════════════════════════════════════════════════════
-- 7. Signal History — Historical values from each graph node
-- ═════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS signal_history (
  id BIGSERIAL PRIMARY KEY,
  timestamp BIGINT NOT NULL,
  symbol VARCHAR(20) NOT NULL,
  node_id VARCHAR(50) NOT NULL,
  node_name VARCHAR(100),
  category VARCHAR(20), -- technical, onchain, sentiment, derivatives, macro
  value REAL NOT NULL,
  confidence REAL NOT NULL,
  weight REAL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_signals_symbol_node_ts ON signal_history(symbol, node_id, timestamp DESC);
CREATE INDEX idx_signals_ts ON signal_history(timestamp DESC);

-- ═════════════════════════════════════════════════════════════════════════════
-- 8. Users (for future multi-user support)
-- ═════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE,
  username VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);

-- ═════════════════════════════════════════════════════════════════════════════
-- 9. Portfolio Positions (snapshot of holdings)
-- ═════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS portfolio_positions (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  symbol VARCHAR(20) NOT NULL,
  quantity REAL DEFAULT 0,
  avg_cost REAL DEFAULT 0,
  current_value REAL DEFAULT 0,
  unrealized_pnl REAL DEFAULT 0,
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_positions_user ON portfolio_positions(user_id);

-- ═════════════════════════════════════════════════════════════════════════════
-- Seed default data
-- ═════════════════════════════════════════════════════════════════════════════

-- Default user
INSERT INTO users (id, email, username) VALUES (1, 'admin@chronos.quantum', 'QuantumAdmin')
ON CONFLICT (id) DO NOTHING;

-- Default strategies
INSERT INTO strategies (name, description, type, parameters) VALUES
  ('SMA Crossover', 'Buy when SMA7 crosses above SMA25, sell on cross below', 'sma_crossover', '{"shortPeriod": 7, "longPeriod": 25}'),
  ('RSI Mean Reversion', 'Buy on RSI oversold (<30), sell on overbought (>70)', 'rsi_reversion', '{"period": 14, "oversold": 30, "overbought": 70}'),
  ('Breakout Momentum', 'Buy on BB upper breakout with volume confirmation', 'breakout_momentum', '{"bbPeriod": 20, "volumeMultiplier": 1.5}'),
  ('BB Squeeze', 'Enter on BB squeeze with ADX confirmation', 'bb_squeeze', '{"bbPeriod": 20, "adxThreshold": 25}'),
  ('Ensemble Graph', 'Uses the full probabilistic graph engine for decisions', 'ensemble_graph', '{"minConfidence": 0.6, "minScore": 65}')
ON CONFLICT DO NOTHING;

-- Default paper wallets
INSERT INTO paper_wallets (name, strategy_id, initial_capital, current_capital, status) VALUES
  ('Alpha — SMA Crossover', 'sma_crossover', 100000, 100000, 'training'),
  ('Beta — RSI Mean Reversion', 'rsi_reversion', 100000, 100000, 'training'),
  ('Gamma — Breakout Momentum', 'breakout_momentum', 100000, 100000, 'training'),
  ('Delta — BB Squeeze', 'bb_squeeze', 100000, 100000, 'training'),
  ('Epsilon — Ensemble (Graph)', 'ensemble_graph', 100000, 100000, 'training')
ON CONFLICT DO NOTHING;

-- Enable Row Level Security (optional, for multi-user future)
-- ALTER TABLE market_snapshots ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE ai_decisions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
