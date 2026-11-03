"""Serializable model bundle uses identical preprocessing for training and inference."""
from dataclasses import dataclass

import numpy as np
from scipy.special import logit


@dataclass
class FraudModel:
    pipeline: object
    calibrator: object
    threshold: float
    background: np.ndarray

    def predict_proba(self, frame):
        raw = np.clip(self.pipeline.predict_proba(frame)[:, 1], 1e-7, 1 - 1e-7)
        return self.calibrator.predict_proba(logit(raw).reshape(-1, 1))[:, 1]

    def transformed(self, frame):
        return self.pipeline[:-1].transform(frame)
