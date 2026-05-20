-- CAGEBOT Analytical Database Schema
-- 6 tables, 3NF normalized


-- ============================================================
-- Table: events
-- ============================================================
CREATE TABLE events (
    id          SERIAL PRIMARY KEY,
    stem        VARCHAR(20) UNIQUE NOT NULL,
    name        VARCHAR(100) NOT NULL,
    date        DATE NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'upcoming',
    model_version VARCHAR(10),
    venue       VARCHAR(100),
    city        VARCHAR(50),
    state       VARCHAR(50),
    country     VARCHAR(50),
    latitude    DECIMAL(9,6),
    longitude   DECIMAL(9,6)
);

-- ============================================================
-- Table: fighters
-- ============================================================
CREATE TABLE fighters (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) UNIQUE NOT NULL,
    stance      VARCHAR(20),
    height_in   DECIMAL(4,1),
    reach_in    DECIMAL(4,1),
    dob         DATE
);

-- ============================================================
-- Table: fights
-- ============================================================
CREATE TABLE fights (
    id              SERIAL PRIMARY KEY,
    event_id        INT NOT NULL REFERENCES events(id),
    fighter_a_id    INT NOT NULL REFERENCES fighters(id),
    fighter_b_id    INT NOT NULL REFERENCES fighters(id),
    model_pick_id   INT NOT NULL REFERENCES fighters(id),
    model_prob      DECIMAL(4,1) NOT NULL,
    predicted_method VARCHAR(20),
    ko_prob         DECIMAL(4,1),
    sub_prob        DECIMAL(4,1),
    dec_prob        DECIMAL(4,1),
    actual_winner_id INT REFERENCES fighters(id),
    finish_method   VARCHAR(20),
    finish_round    INT,
    finish_time     VARCHAR(10),
    CONSTRAINT uq_fights_event_fighters UNIQUE (event_id, fighter_a_id, fighter_b_id)
);

-- ============================================================
-- Table: odds_snapshots
-- ============================================================
CREATE TABLE odds_snapshots (
    id              SERIAL PRIMARY KEY,
    fight_id        INT NOT NULL REFERENCES fights(id),
    bookmaker       VARCHAR(30) NOT NULL DEFAULT 'consensus',
    odds            DECIMAL(6,3),
    implied_pct     DECIMAL(5,2),
    snapshot_type   VARCHAR(15) NOT NULL,
    captured_at     TIMESTAMP,
    CONSTRAINT uq_odds_fight_type_book UNIQUE (fight_id, snapshot_type, bookmaker)
);

-- ============================================================
-- Table: overrides
-- ============================================================
CREATE TABLE overrides (
    id              SERIAL PRIMARY KEY,
    fight_id        INT UNIQUE NOT NULL REFERENCES fights(id),
    override_pick_id INT NOT NULL REFERENCES fighters(id),
    notes           TEXT
);

-- ============================================================
-- Table: fighter_elo_history
-- ============================================================
CREATE TABLE fighter_elo_history (
    id              SERIAL PRIMARY KEY,
    fighter_id      INT NOT NULL REFERENCES fighters(id),
    event_date      DATE NOT NULL,
    event_name      VARCHAR(150),
    elo_before      DECIMAL(6,1) NOT NULL,
    elo_after       DECIMAL(6,1) NOT NULL,
    elo_delta       DECIMAL(5,1) NOT NULL,
    elo_fights      INT NOT NULL,
    opponent_name   VARCHAR(100),
    result          VARCHAR(10),
    CONSTRAINT uq_elo_fighter_date UNIQUE (fighter_id, event_date)
);

-- ============================================================
-- Indexes
-- ============================================================
CREATE INDEX idx_fights_event_id ON fights(event_id);
CREATE INDEX idx_fights_model_pick_id ON fights(model_pick_id);
CREATE INDEX idx_fights_actual_winner_id ON fights(actual_winner_id);
CREATE INDEX idx_odds_fight_id ON odds_snapshots(fight_id);
CREATE INDEX idx_elo_fighter_id ON fighter_elo_history(fighter_id);
CREATE INDEX idx_elo_date ON fighter_elo_history(event_date);
CREATE INDEX idx_events_date ON events(date);
