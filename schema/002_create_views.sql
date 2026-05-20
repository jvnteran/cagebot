-- CAGEBOT Analytical Views
-- 4 views computing accuracy metrics on the fly
-- Generated from spec: docs/superpowers/specs/2026-05-20-postgresql-analytical-database-design.md

-- ============================================================
-- View: v_event_accuracy
-- Replaces pre-computed columns in master_events.csv
-- ============================================================
CREATE VIEW v_event_accuracy AS
SELECT
    e.id, e.stem, e.name, e.date, e.model_version,
    e.venue, e.city, e.country, e.latitude, e.longitude,
    COUNT(*) AS decided_fights,
    COUNT(*) FILTER (WHERE f.actual_winner_id = f.model_pick_id) AS model_correct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE f.actual_winner_id = f.model_pick_id)
          / COUNT(*), 1) AS model_accuracy_pct,
    COUNT(ov.id) AS override_count,
    COUNT(ov.id) FILTER (WHERE ov.override_pick_id = f.actual_winner_id) AS override_correct,
    COUNT(ov.id) FILTER (WHERE ov.override_pick_id != f.actual_winner_id) AS override_wrong,
    COUNT(*) FILTER (WHERE
        COALESCE(ov.override_pick_id, f.model_pick_id) = f.actual_winner_id
    ) AS combined_correct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE
        COALESCE(ov.override_pick_id, f.model_pick_id) = f.actual_winner_id
    ) / COUNT(*), 1) AS combined_accuracy_pct,
    ROUND(AVG(f.model_prob), 1) AS avg_model_prob,
    ROUND(AVG(os_open.implied_pct), 1) AS avg_market_implied
FROM fights f
JOIN events e ON f.event_id = e.id
LEFT JOIN overrides ov ON ov.fight_id = f.id
LEFT JOIN odds_snapshots os_open ON os_open.fight_id = f.id
    AND os_open.snapshot_type = 'opening' AND os_open.bookmaker = 'consensus'
WHERE f.actual_winner_id IS NOT NULL
  AND f.finish_method NOT IN ('NC', 'Cancelled', 'DRAW')
GROUP BY e.id, e.stem, e.name, e.date, e.model_version,
         e.venue, e.city, e.country, e.latitude, e.longitude;

-- ============================================================
-- View: v_fight_detail
-- One query gets everything — main Streamlit data source
-- ============================================================
CREATE VIEW v_fight_detail AS
SELECT
    e.stem, e.name AS event_name, e.date AS event_date,
    e.venue, e.city, e.country,
    fa.name AS fighter_a, fb.name AS fighter_b,
    mp.name AS model_pick, f.model_prob,
    f.predicted_method, f.ko_prob, f.sub_prob, f.dec_prob,
    CASE WHEN ov.id IS NOT NULL THEN 'OVERRIDE' ELSE 'MODEL' END AS source,
    op.name AS override_pick,
    w.name AS actual_winner,
    f.actual_winner_id = f.model_pick_id AS model_correct,
    COALESCE(ov.override_pick_id, f.model_pick_id) = f.actual_winner_id AS combined_correct,
    f.finish_method, f.finish_round, f.finish_time,
    os_open.odds AS opening_odds, os_open.implied_pct AS opening_implied,
    os_close.odds AS closing_odds, os_close.implied_pct AS closing_implied,
    f.model_prob - os_open.implied_pct AS edge,
    os_close.implied_pct - os_open.implied_pct AS clv_pp
FROM fights f
JOIN events e ON f.event_id = e.id
JOIN fighters fa ON f.fighter_a_id = fa.id
JOIN fighters fb ON f.fighter_b_id = fb.id
JOIN fighters mp ON f.model_pick_id = mp.id
LEFT JOIN fighters w ON f.actual_winner_id = w.id
LEFT JOIN overrides ov ON ov.fight_id = f.id
LEFT JOIN fighters op ON ov.override_pick_id = op.id
LEFT JOIN odds_snapshots os_open ON os_open.fight_id = f.id
    AND os_open.snapshot_type = 'opening' AND os_open.bookmaker = 'consensus'
LEFT JOIN odds_snapshots os_close ON os_close.fight_id = f.id
    AND os_close.snapshot_type = 'closing' AND os_close.bookmaker = 'consensus';

-- ============================================================
-- View: v_fighter_current
-- Current fighter state — latest ELO and last fight date
-- ============================================================
CREATE VIEW v_fighter_current AS
SELECT DISTINCT ON (h.fighter_id)
    fi.id, fi.name, fi.stance, fi.height_in, fi.reach_in,
    h.elo_after AS current_elo,
    h.elo_fights,
    h.event_date AS last_fight_date
FROM fighter_elo_history h
JOIN fighters fi ON h.fighter_id = fi.id
ORDER BY h.fighter_id, h.event_date DESC;

-- ============================================================
-- View: v_accuracy_by_location
-- Powers the map chart in Streamlit
-- ============================================================
CREATE VIEW v_accuracy_by_location AS
SELECT
    e.city, e.country, e.latitude, e.longitude,
    COUNT(DISTINCT e.id) AS events,
    COUNT(*) AS decided_fights,
    COUNT(*) FILTER (WHERE f.actual_winner_id = f.model_pick_id) AS model_correct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE f.actual_winner_id = f.model_pick_id)
          / COUNT(*), 1) AS accuracy_pct
FROM fights f
JOIN events e ON f.event_id = e.id
WHERE f.actual_winner_id IS NOT NULL
  AND f.finish_method NOT IN ('NC', 'Cancelled', 'DRAW')
  AND e.latitude IS NOT NULL
GROUP BY e.city, e.country, e.latitude, e.longitude;
