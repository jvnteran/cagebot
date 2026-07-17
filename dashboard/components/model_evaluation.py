"""Pure model-evaluation calculations shared by the Streamlit dashboard."""

from __future__ import annotations

import numpy as np
import pandas as pd


def rank_auc(scores, labels) -> float:
    """Return Mann-Whitney ROC AUC with half-credit for tied scores."""
    positives = [score for score, label in zip(scores, labels) if label == 1]
    negatives = [score for score, label in zip(scores, labels) if label == 0]
    if not positives or not negatives:
        return 0.5

    wins = 0.0
    for positive in positives:
        for negative in negatives:
            if positive > negative:
                wins += 1.0
            elif positive == negative:
                wins += 0.5
    return wins / (len(positives) * len(negatives))


def compute_discrimination_auc(df: pd.DataFrame) -> float:
    """Calculate live ROC AUC using probabilities oriented to fighter A."""
    probability = pd.to_numeric(df["model_prob"], errors="raise").to_numpy() / 100.0
    fighter_a = df["fighter_a"].astype(str).str.strip().str.casefold()
    picked_a = (
        df["model_pick"].astype(str).str.strip().str.casefold() == fighter_a
    ).to_numpy()
    fighter_a_won = (
        df["actual_winner"].astype(str).str.strip().str.casefold() == fighter_a
    ).astype(int).to_numpy()
    probability_a = np.where(picked_a, probability, 1.0 - probability)
    return rank_auc(probability_a, fighter_a_won)
