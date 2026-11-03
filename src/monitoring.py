"""Reference drift checks; alarms are diagnostics rather than performance claims."""
import numpy as np
from scipy.stats import ks_2samp
from src.data import CATEGORIES, NUMERIC


def drift_report(reference, current) -> dict:
    numeric = {}
    for col in NUMERIC:
        a, b = reference[col].dropna(), current[col].dropna()
        if len(a) and len(b):
            statistic, p = ks_2samp(a, b)
            numeric[col] = {"ks_statistic": float(statistic), "p_value": float(p), "warning": bool(statistic > .15)}
    categorical = {}
    for col in CATEGORIES:
        a, b = reference[col].fillna("Missing").value_counts(normalize=True), current[col].fillna("Missing").value_counts(normalize=True)
        cats = a.index.union(b.index)
        distance = float(np.abs(a.reindex(cats, fill_value=0) - b.reindex(cats, fill_value=0)).sum() / 2)
        categorical[col] = {"total_variation": distance, "warning": distance > .15}
    return {"numeric": numeric, "categorical": categorical, "reference_rows": len(reference), "current_rows": len(current), "note": "KS > 0.15 or total variation > 0.15 triggers a diagnostic warning. No live performance monitoring without delayed labels."}
