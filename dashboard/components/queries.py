"""Pre-built SQL queries for the SQL Explorer page."""

QUERIES = {
    "How accurate is the model per event?": {
        "sql": """SELECT name AS event, date, decided_fights, model_correct,
       model_accuracy_pct, combined_correct, combined_accuracy_pct,
       override_count
FROM v_event_accuracy
ORDER BY date;""",
        "description": "Shows accuracy at every UFC event since launch. The 'combined' column "
                       "includes founder overrides — fights where human judgment corrected the model.",
    },
    "What does a fighter's ELO career look like?": {
        "sql": """SELECT f.name AS fighter, h.event_date, h.event_name,
       h.elo_before, h.elo_after, h.elo_delta,
       h.opponent_name, h.result
FROM fighter_elo_history h
JOIN fighters f ON h.fighter_id = f.id
WHERE f.name = 'islam makhachev'
ORDER BY h.event_date;""",
        "description": "Traces a fighter's complete ELO rating history — every fight, every opponent, "
                       "every win and loss. Change the name to explore any fighter in the database.",
    },
    "Which fight outcomes does the model predict best?": {
        "sql": """SELECT finish_method,
       COUNT(*) AS fights,
       COUNT(*) FILTER (WHERE actual_winner_id = model_pick_id) AS correct,
       ROUND(100.0 * COUNT(*) FILTER (WHERE actual_winner_id = model_pick_id)
             / COUNT(*), 1) AS accuracy_pct
FROM fights
WHERE actual_winner_id IS NOT NULL
  AND finish_method NOT IN ('NC', 'Cancelled', 'DRAW')
GROUP BY finish_method
ORDER BY fights DESC;""",
        "description": "Breaks down accuracy by how the fight ended — KO/TKO, submission, or decision. "
                       "Reveals whether the model is better at predicting finishes vs decisions.",
    },
    "Did the founder's overrides actually help?": {
        "sql": """SELECT e.name AS event, fa.name AS fighter_a, fb.name AS fighter_b,
       mp.name AS model_pick, op.name AS override_pick,
       w.name AS actual_winner,
       (f.actual_winner_id = f.model_pick_id) AS model_was_right,
       (ov.override_pick_id = f.actual_winner_id) AS override_was_right
FROM overrides ov
JOIN fights f ON ov.fight_id = f.id
JOIN events e ON f.event_id = e.id
JOIN fighters fa ON f.fighter_a_id = fa.id
JOIN fighters fb ON f.fighter_b_id = fb.id
JOIN fighters mp ON f.model_pick_id = mp.id
JOIN fighters op ON ov.override_pick_id = op.id
LEFT JOIN fighters w ON f.actual_winner_id = w.id
ORDER BY e.date;""",
        "description": "Every time the founder disagreed with the model and picked a different fighter. "
                       "Shows whether the human correction helped or hurt — the core question behind "
                       "human-in-the-loop ML.",
    },
    "Which events were the best and worst?": {
        "sql": """SELECT name AS event, date, decided_fights,
       model_correct, model_accuracy_pct,
       combined_correct, combined_accuracy_pct
FROM v_event_accuracy
ORDER BY combined_accuracy_pct DESC;""",
        "description": "Ranks all events from best to worst prediction accuracy. "
                       "Shows the variance in performance — some cards are easier to predict than others.",
    },
    "Where did the model disagree with the market?": {
        "sql": """SELECT event_name, fighter_a, fighter_b,
       model_pick, model_prob, opening_implied AS market_implied,
       edge, actual_winner, model_correct
FROM v_fight_detail
WHERE edge IS NOT NULL AND ABS(edge) > 10
ORDER BY ABS(edge) DESC;""",
        "description": "Fights where the model's confidence diverged from market odds by more than 10 "
                       "percentage points. These contrarian picks are where the model sees value "
                       "that the betting market doesn't.",
    },
}
