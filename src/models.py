"""The learned rung: one gradient-boosted regressor per target column.

Extracted because the fit-clip-renormalize block appeared four times (once in
`06_analysis` for the Tier-1 shares, three times in `08_human_cause` for the
Human sub-cause rungs) and carries an invariant worth asserting once: predictions
must land back on the simplex.

Only `SimplexRegressor` is wrapped. The scalar targets -- the Tier-1 level and the
Natural branch -- call `HistGradientBoostingRegressor` directly in the notebooks
with per-rung hyperparameters (`max_depth=3` in 07, `max_iter=400` for the level).
Wrapping eight lines of sklearn glue whose only job is to obscure those numbers
would be a net loss: the hyperparameters are part of the visible method.
"""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor


class SimplexRegressor:
    """Per-column gradient boosting, with predictions projected onto the simplex.

    A composition target cannot be fit as a unit by a scalar regressor, so each
    class/sub-cause gets its own model. Independent models do not respect the
    simplex constraint, so predictions are clipped at zero and divided by their
    row sum -- the projection the notebooks apply and this class asserts.

    Defaults match the settings used in `06_analysis` and `08_human_cause`
    (max_iter=300, learning_rate=0.05, max_leaf_nodes=31, random_state=0), so the
    seeded results stay reproducible.
    """

    def __init__(
        self,
        *,
        max_iter: int = 300,
        learning_rate: float = 0.05,
        max_leaf_nodes: int = 31,
        random_state: int = 0,
        **kwargs,
    ):
        self.params = dict(
            max_iter=max_iter,
            learning_rate=learning_rate,
            max_leaf_nodes=max_leaf_nodes,
            random_state=random_state,
            **kwargs,
        )
        self.models_: list[HistGradientBoostingRegressor] = []

    def __repr__(self) -> str:
        state = f"{len(self.models_)} fitted" if self.models_ else "unfitted"
        return f"SimplexRegressor({state}, max_iter={self.params['max_iter']})"

    def fit(self, X: np.ndarray, Y: np.ndarray, sample_weight=None) -> "SimplexRegressor":
        """Fit one regressor per column of `Y`.

        `sample_weight` is passed through to every column's model -- the notebooks
        weight training by acres so the fit reflects where the burned area is.
        """
        Y = np.asarray(Y, dtype=float)
        if Y.ndim != 2:
            raise ValueError(f"Y must be 2-D (rows x classes), got shape {Y.shape}")
        self.models_ = []
        for j in range(Y.shape[1]):
            model = HistGradientBoostingRegressor(**self.params)
            model.fit(X, Y[:, j], sample_weight=sample_weight)
            self.models_.append(model)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict, then project onto the simplex (clip negatives, renormalize)."""
        if not self.models_:
            raise RuntimeError("SimplexRegressor must be fit before predict")
        raw = np.vstack([m.predict(X) for m in self.models_]).T
        out = np.clip(raw, 0, None)

        row_sums = out.sum(axis=1, keepdims=True)
        if not np.all(row_sums > 0):
            # Every class clipped to zero: no basis for a composition. Surfacing this
            # beats emitting silent NaNs from a divide-by-zero.
            raise ValueError(
                f"{int((row_sums <= 0).sum())} rows had all classes clipped to zero; "
                "cannot renormalize onto the simplex"
            )
        out = out / row_sums
        assert np.allclose(out.sum(axis=1), 1.0), "projection failed to reach the simplex"
        return out
