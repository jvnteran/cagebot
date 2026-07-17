"""Regression tests for live dashboard model-evaluation metrics."""

import pandas as pd
import pytest

from dashboard.components.model_evaluation import (
    compute_discrimination_auc,
    rank_auc,
)


def test_auc_orients_pick_confidence_to_fighter_a():
    rows = pd.DataFrame(
        [
            {
                "fighter_a": "A1",
                "model_pick": "A1",
                "actual_winner": "A1",
                "model_prob": 90.0,
            },
            {
                "fighter_a": "A2",
                "model_pick": "B2",
                "actual_winner": "B2",
                "model_prob": 80.0,
            },
            {
                "fighter_a": "A3",
                "model_pick": "A3",
                "actual_winner": "B3",
                "model_prob": 60.0,
            },
            {
                "fighter_a": "A4",
                "model_pick": "B4",
                "actual_winner": "A4",
                "model_prob": 55.0,
            },
        ]
    )

    assert compute_discrimination_auc(rows) == pytest.approx(0.75)


def test_auc_name_orientation_ignores_case_and_surrounding_whitespace():
    rows = pd.DataFrame(
        [
            {
                "fighter_a": "  Fighter One ",
                "model_pick": "fighter one",
                "actual_winner": "FIGHTER ONE",
                "model_prob": 80.0,
            },
            {
                "fighter_a": "Fighter Two",
                "model_pick": "opponent two",
                "actual_winner": "opponent two",
                "model_prob": 70.0,
            },
        ]
    )

    assert compute_discrimination_auc(rows) == pytest.approx(1.0)


def test_rank_auc_awards_half_credit_for_ties():
    assert rank_auc([0.7, 0.7], [1, 0]) == pytest.approx(0.5)


def test_rank_auc_returns_neutral_value_for_single_class():
    assert rank_auc([0.8, 0.6], [1, 1]) == pytest.approx(0.5)
