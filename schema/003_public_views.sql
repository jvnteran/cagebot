-- CAGEBOT — public reporting surface for the Market Performance page.
--
-- The dashboard is only ever granted SELECT on the views defined here. Every
-- one of them is an aggregate or a model-level record: none exposes an
-- individual staking decision (which fight, which side, what size), because
-- those rows are the strategy itself.
--
-- v_market_audit below is the real definition — it is derived entirely from
-- v_fight_detail and contains nothing but model output priced against public
-- market lines.
--
-- The three strategy-side views are backed in production by tables that live
-- with the private prediction engine and are not part of this repository. The
-- stand-in tables here carry the same output columns so the dashboard runs
-- against a local database; populate them with your own records.


-- ============================================================
-- View: v_market_audit  (production definition)
-- Model picks priced at the opening and closing line. Decided fights only,
-- matching the mask used by the Model Evaluation page.
-- ============================================================
CREATE VIEW v_market_audit AS
SELECT event_date, model_prob, opening_odds, opening_implied,
       closing_odds, closing_implied, clv_pp, edge, model_correct
FROM v_fight_detail
WHERE actual_winner IS NOT NULL
  AND model_correct IS NOT NULL
  AND model_prob IS NOT NULL
  AND upper(btrim(actual_winner)) NOT IN
      ('NC', 'DRAW', 'NO CONTEST', 'CANCELLED')
  AND upper(btrim(coalesce(finish_method, ''))) NOT IN
      ('NC', 'CNC', 'CANCELLED', 'NO CONTEST', 'OVERTURNED');


-- ============================================================
-- Local stand-ins for the strategy-side surface.
-- Settled record, summed only. No fight, side, or price column exists here
-- by design — the dashboard cannot render what the schema does not carry.
-- ============================================================
CREATE TABLE strategy_record (
    id          SERIAL PRIMARY KEY,
    event_date  DATE NOT NULL,
    units       DECIMAL(6,2) NOT NULL,
    result      VARCHAR(4) NOT NULL CHECK (result IN ('W', 'L')),
    pl_units    DECIMAL(8,2) NOT NULL
);

CREATE VIEW v_strategy_record_public AS
SELECT event_date, units, result, pl_units
FROM strategy_record;


-- Per-trigger aggregates. Triggers carry anonymous display labels only; the
-- rules behind them are not represented in this schema.
CREATE TABLE trigger_summary (
    trigger_label   VARCHAR(40) PRIMARY KEY,
    bt_hit_rate     DECIMAL(5,4),
    bt_n            INTEGER,
    live_graded     INTEGER DEFAULT 0,
    live_wins       INTEGER DEFAULT 0,
    live_pl_units   DECIMAL(8,2) DEFAULT 0
);

CREATE VIEW v_markets_ev_public AS
SELECT trigger_label, bt_hit_rate, bt_n, live_graded, live_wins, live_pl_units
FROM trigger_summary;


-- Funnel counts for the derivative-pricing experiment: totals at each stage,
-- never the qualifying condition.
CREATE TABLE markets_funnel (
    id                      SERIAL PRIMARY KEY,
    priced_outcomes         INTEGER NOT NULL,
    market_groups           INTEGER NOT NULL,
    events_covered          INTEGER NOT NULL,
    graded_outcomes         INTEGER NOT NULL,
    qualified_bets          INTEGER NOT NULL,
    qualified_graded        INTEGER NOT NULL,
    qualified_wins          INTEGER NOT NULL,
    qualified_pl_units      DECIMAL(10,2) NOT NULL,
    unfiltered_pl_units     DECIMAL(12,2) NOT NULL,
    qualified_prop_clv_avg  DECIMAL(6,2) NOT NULL,
    qualified_prop_moved    INTEGER NOT NULL
);

CREATE VIEW v_markets_funnel_public AS
SELECT priced_outcomes, market_groups, events_covered, graded_outcomes,
       qualified_bets, qualified_graded, qualified_wins, qualified_pl_units,
       unfiltered_pl_units, qualified_prop_clv_avg, qualified_prop_moved
FROM markets_funnel;


-- ============================================================
-- Grants — the web role reads views, never base tables.
-- ============================================================
-- CREATE ROLE dashboard_ro LOGIN PASSWORD 'set-me';
-- GRANT SELECT ON v_event_accuracy, v_fight_detail, v_fighter_current,
--                v_accuracy_by_location, v_market_audit,
--                v_strategy_record_public, v_markets_ev_public,
--                v_markets_funnel_public
--   TO dashboard_ro;
-- REVOKE ALL ON strategy_record, trigger_summary, markets_funnel
--   FROM dashboard_ro;
