"""Real additive SHAP values in the underlying estimator's native output space."""
import numpy as np
import shap
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier


class Explainer:
    def __init__(self, bundle):
        self.bundle = bundle
        estimator = bundle.pipeline.named_steps["model"]
        self.names = bundle.pipeline.named_steps["preprocess"].get_feature_names_out().tolist()
        if isinstance(estimator, LogisticRegression):
            self.explainer = shap.LinearExplainer(estimator, bundle.background)
            self.space = "uncalibrated log odds"
        else:
            self.explainer = shap.TreeExplainer(estimator)
            self.space = "uncalibrated probability" if isinstance(estimator, RandomForestClassifier) else "uncalibrated log odds"

    def values(self, frame):
        explanation = self.explainer(self.bundle.transformed(frame))
        values = np.asarray(explanation.values)
        bases = np.asarray(explanation.base_values)
        if values.ndim == 3:
            values, bases = values[:, :, 1], bases[:, 1]
        return values, bases

    def local(self, frame) -> dict:
        values, bases = self.values(frame)
        contributions = values[0]
        indices = np.argsort(-np.abs(contributions))[:8]
        transformed = self.bundle.transformed(frame)[0]
        return {
            "method": "SHAP", "output_space": self.space,
            "note": "Contributions explain the base estimator, before sigmoid calibration. Association is not causation.",
            "base_value": float(np.ravel(bases)[0]),
            "explained_output": float(np.ravel(bases)[0] + contributions.sum()),
            "factors": [{"feature": self.names[i], "contribution": float(contributions[i]), "transformed_value": float(transformed[i])} for i in indices],
        }

    def global_importance(self, frame) -> list[dict]:
        values, _ = self.values(frame)
        magnitude = np.abs(values).mean(axis=0)
        return [{"feature": self.names[i], "mean_absolute_shap": float(magnitude[i])} for i in np.argsort(-magnitude)]
