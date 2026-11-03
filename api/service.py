"""Read-only offline investigation store. No customer IDs or raw labels enter scoring."""
import json
import os
import threading

import joblib
import numpy as np
import pandas as pd

from src.config import dataset_path, model_dir, risk_boundaries
from src.data import FEATURES, Transaction, inference_frame, load_financial
from src.explain import Explainer


class FraudService:
    def __init__(self):
        directory = model_dir()
        # Only load trusted local artifacts produced by scripts.train; never accept uploads.
        self.metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
        self.bundle = joblib.load(directory / "fraud_pipeline.joblib")
        self.threshold = float(os.getenv("FRAUD_THRESHOLD") or self.bundle.threshold)
        if not 0 <= self.threshold <= np.nextafter(1., 2.):
            raise ValueError("Invalid threshold override")
        self.boundaries = risk_boundaries()
        self.frame, self.quality = load_financial(dataset_path())
        import hashlib
        if hashlib.sha256(dataset_path().read_bytes()).hexdigest() != self.metadata["dataset_version"]:
            raise ValueError("Dataset version differs from model metadata; retrain before serving")
        self.explainer = Explainer(self.bundle)
        self.explanation_lock = threading.Lock()
        self.frame["fraud_probability"] = self.bundle.predict_proba(self.frame[FEATURES])
        self.frame["risk_score"] = self.frame.fraud_probability * 100
        self.frame["predicted_class"] = (self.frame.fraud_probability >= self.threshold).astype(int)
        self.frame["risk_category"] = self.frame.risk_score.map(self.category)
        test_ids = set(pd.read_csv(directory / "test_ids.csv").Transaction_ID)
        self.frame["evaluation_cohort"] = np.where(self.frame.Transaction_ID.isin(test_ids), "test", "development")

    def category(self, score: float) -> str:
        return ["Low", "Moderate", "High", "Critical"][int(np.searchsorted(self.boundaries, score, side="right"))]

    def predict(self, transactions: list[Transaction], explain: bool = True) -> list[dict]:
        frame = inference_frame([record.model_dump() for record in transactions])
        probabilities = self.bundle.predict_proba(frame)
        results = []
        for i, p in enumerate(probabilities):
            warnings = []
            if frame.iloc[i].isna().any():
                warnings.append("Missing optional values were imputed using the fitted training pipeline.")
            if frame.iloc[i].Transaction_Amount > self.metadata["amount_reference_quantiles"][2]:
                warnings.append("Amount exceeds training 99th percentile; this is a distribution warning, not a fraud explanation.")
            if explain:
                with self.explanation_lock:
                    explanation = self.explainer.local(frame.iloc[[i]])
            else:
                explanation = None
            results.append({"fraud_probability": float(p), "risk_score": float(p * 100), "predicted_class": int(p >= self.threshold), "risk_category": self.category(p * 100), "threshold": self.threshold, "model_version": self.metadata["model_version"], "warnings": warnings, "explanation": explanation})
        return results

    def record(self, transaction_id):
        rows = self.frame[self.frame.Transaction_ID == transaction_id]
        return None if rows.empty else rows.iloc[0]

    @staticmethod
    def serialize(frame):
        columns = ["Transaction_ID", *FEATURES, "Fraudulent", "fraud_probability", "risk_score", "predicted_class", "risk_category", "evaluation_cohort"]
        result = frame[columns].copy()
        result["Transaction_Date"] = result.Transaction_Date.dt.strftime("%Y-%m-%dT%H:%M:%S")
        return json.loads(result.to_json(orient="records"))

    def cohort(self, name):
        return self.frame if name == "all" else self.frame[self.frame.evaluation_cohort == name]

    def overview(self, cohort="test"):
        frame = self.cohort(cohort)
        return {"cohort": cohort, "total_transactions": len(frame), "fraudulent_transactions": int(frame.Fraudulent.sum()), "fraud_rate": float(frame.Fraudulent.mean()), "total_value": float(frame.Transaction_Amount.sum()), "observed_fraud_value": float(frame.loc[frame.Fraudulent == 1, "Transaction_Amount"].sum()), "estimated_exposure": float((frame.Transaction_Amount * frame.fraud_probability).sum()), "average_amount": float(frame.Transaction_Amount.mean()), "flagged_transactions": int(frame.predicted_class.sum()), "date_start": str(frame.Transaction_Date.min()), "date_end": str(frame.Transaction_Date.max()), "currency": "Unspecified dataset units", "recent_fraud": self.serialize(frame[frame.Fraudulent == 1].sort_values("Transaction_Date", ascending=False).head(6)), "note": "Offline labeled dataset. Default cohort is held-out test. Expected exposure = sum(amount x calibrated probability), not realized loss."}

    def analytics(self, cohort="test"):
        frame = self.cohort(cohort)
        def grouped(key):
            grouped = frame.groupby(key, observed=True).agg(transactions=("Fraudulent", "size"), fraud=("Fraudulent", "sum"), fraud_rate=("Fraudulent", "mean"), flagged=("predicted_class", "sum"), value=("Transaction_Amount", "sum"))
            return [{"name": str(name), **{k: float(v) for k, v in row.items()}} for name, row in grouped.iterrows()]
        month = frame.Transaction_Date.dt.strftime("%Y-%m")
        monthly = grouped(month)
        for row in monthly:
            selected = frame.loc[month == row["name"]]
            row["fraud_value"] = float(selected.loc[selected.Fraudulent == 1, "Transaction_Amount"].sum())
            row["high_risk"] = int((selected.risk_score >= self.boundaries[1]).sum())
        counts, edges = np.histogram(frame.fraud_probability, bins=np.linspace(0, 1, 11))
        return {"cohort": cohort, "monthly": monthly, "by_type": grouped("Merchant_Category"), "by_payment": grouped("Payment_Method"), "by_location": grouped("Location"), "by_amount": grouped(pd.cut(frame.Transaction_Amount, [-.01, 25, 50, 100, 200, np.inf], labels=["0-25", "25-50", "50-100", "100-200", "200+"])), "probability_distribution": [{"name": f"{edges[i]:.1f}-{edges[i+1]:.1f}", "count": int(n)} for i, n in enumerate(counts)]}
