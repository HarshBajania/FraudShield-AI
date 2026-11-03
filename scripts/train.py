"""Reproducible chronological experiment. Run from repository root with python -m scripts.train."""
import hashlib
import json
import platform
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
import sklearn
from scipy.special import logit
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score

from src.config import dataset_path, model_dir, training_config
from src.data import FEATURES, load_financial
from src.evaluation import curves, evaluate, select_threshold
from src.explain import Explainer
from src.features import make_pipeline
from src.model import FraudModel
from src.monitoring import drift_report


def split_windows(frame, fractions):
    """Split whole calendar days so simultaneous transactions cannot span windows."""
    days = np.sort(frame.Transaction_Date.dt.normalize().unique())
    boundaries = [days[min(len(days) - 1, int(v * len(days)))] for v in np.cumsum(fractions)[:-1]]
    assignments = np.searchsorted(boundaries, frame.Transaction_Date.dt.normalize(), side="right")
    windows = [frame.loc[assignments == i].copy() for i in range(5)]
    for window in windows:
        if window.Fraudulent.nunique() != 2:
            raise ValueError("Each chronological window needs both classes; adjust fractions")
    return windows


def bootstrap_metrics(y, p, seed):
    """Fixed-model test uncertainty, not a claim about training variability."""
    rng = np.random.default_rng(seed)
    aps = []
    for _ in range(300):
        indices = rng.integers(0, len(y), len(y))
        if len(np.unique(y[indices])) == 2:
            aps.append(average_precision_score(y[indices], p[indices]))
    return {"pr_auc_95_percentile_interval": np.quantile(aps, [.025, .975]).tolist(), "resamples": len(aps)}


def train():
    config = training_config()
    frame, quality = load_financial(dataset_path())
    fit, tune, calibration, policy, test = split_windows(frame, config["split_fractions"])
    seed = config["seed"]
    candidates = {
        "Logistic regression": [LogisticRegression(C=c, max_iter=2000, random_state=seed) for c in [.1, 1]],
        "Weighted logistic regression": [LogisticRegression(C=c, class_weight="balanced", max_iter=2000, random_state=seed) for c in [.1, 1]],
        "Random forest": [RandomForestClassifier(n_estimators=150, max_depth=d, min_samples_leaf=12, n_jobs=-1, random_state=seed) for d in [5, 10]],
        "Weighted random forest": [RandomForestClassifier(n_estimators=150, max_depth=d, min_samples_leaf=12, class_weight="balanced", n_jobs=-1, random_state=seed) for d in [5, 10]],
        "Gradient boosting": [GradientBoostingClassifier(n_estimators=100, max_depth=d, learning_rate=.05, min_samples_leaf=15, random_state=seed) for d in [1, 2]],
    }
    comparison, bundles, tuning = [], {}, []
    for name, estimators in candidates.items():
        print(f"Training {name}", flush=True)
        runs = []
        for estimator in estimators:
            pipeline = make_pipeline(estimator).fit(fit[FEATURES], fit.Fraudulent)
            ap = float(average_precision_score(tune.Fraudulent, pipeline.predict_proba(tune[FEATURES])[:, 1]))
            tuning.append({"model": name, "parameters": estimator.get_params(), "tuning_pr_auc": ap})
            runs.append((ap, pipeline))
        ap, pipeline = max(runs, key=lambda pair: pair[0])
        p = np.clip(pipeline.predict_proba(calibration[FEATURES])[:, 1], 1e-7, 1 - 1e-7)
        sigmoid = LogisticRegression(C=1e6, max_iter=1000, random_state=seed).fit(logit(p).reshape(-1, 1), calibration.Fraudulent)
        background = pipeline[:-1].transform(fit[FEATURES].sample(min(100, len(fit)), random_state=seed))
        bundle = FraudModel(pipeline, sigmoid, .5, background)
        scores = bundle.predict_proba(policy[FEATURES])
        threshold, analysis = select_threshold(policy.Fraudulent.to_numpy(), scores, policy.Transaction_Amount.to_numpy(), config)
        bundle.threshold = threshold
        metrics = evaluate(policy.Fraudulent, scores, policy.Transaction_Amount, threshold, config)
        comparison.append({"model": name, "tuning_pr_auc": ap, "policy_metrics": metrics})
        bundles[name] = (bundle, analysis)
    winner = min(comparison, key=lambda row: (row["policy_metrics"]["estimated_cost"], -row["policy_metrics"]["pr_auc"]))
    bundle, threshold_analysis = bundles[winner["model"]]
    scores = bundle.predict_proba(test[FEATURES])
    test_metrics = evaluate(test.Fraudulent, scores, test.Transaction_Amount, bundle.threshold, config)
    # Honest no-signal comparator fitted on training prevalence, policy selected independently.
    baseline_policy = np.full(len(policy), fit.Fraudulent.mean())
    base_threshold, _ = select_threshold(policy.Fraudulent.to_numpy(), baseline_policy, policy.Transaction_Amount.to_numpy(), config)
    baseline = evaluate(test.Fraudulent, np.full(len(test), fit.Fraudulent.mean()), test.Transaction_Amount, base_threshold, config)
    explanation = Explainer(bundle)
    windows = {name: {"rows": len(part), "fraud": int(part.Fraudulent.sum()), "start": str(part.Transaction_Date.min()), "end": str(part.Transaction_Date.max())} for name, part in zip(["fit", "tune", "calibration", "policy", "test"], [fit, tune, calibration, policy, test])}
    metadata = {
        "model_name": winner["model"], "model_version": "1.0.0",
        "training_date": datetime.now(timezone.utc).isoformat(),
        "dataset_version": hashlib.sha256(dataset_path().read_bytes()).hexdigest(),
        "dataset_file": dataset_path().name, "features": FEATURES,
        "threshold": bundle.threshold, "training_config": config,
        "selected_parameters": bundle.pipeline.named_steps["model"].get_params(),
        "libraries": {"python": platform.python_version(), "sklearn": sklearn.__version__, "pandas": pd.__version__, "numpy": np.__version__},
        "split_windows": windows, "data_quality": quality,
        "test_metrics": test_metrics, "test_uncertainty": bootstrap_metrics(test.Fraudulent.to_numpy(), scores, seed),
        "constant_baseline_test": baseline,
        "model_comparison": comparison, "tuning_runs": tuning,
        "threshold_analysis": threshold_analysis[::max(1, len(threshold_analysis) // 150)],
        "curves": curves(test.Fraudulent, scores),
        "global_explanations": explanation.global_importance(test[FEATURES].iloc[:min(200, len(test))]),
        "drift": drift_report(fit, test),
        "amount_reference_quantiles": fit.Transaction_Amount.quantile([.01, .5, .99]).tolist(),
        "selection_reason": "Lowest cost on policy window under review-capacity constraint; tuning by PR-AUC, calibration on separate window; test untouched until selection.",
        "limitations": ["Dataset origin, currency, timezone and label-generation mechanism are undocumented.", "Offline estimates; no claim of production effectiveness.", "Historical features and suspicious keyword excluded due to unknown point-in-time provenance.", "Customer identifiers excluded; chronological evaluation covers recurring customers, not customer-disjoint generalization.", "Probabilities calibrated on a small window; risk bands are configurable presentation conventions.", "SHAP explains base estimator output before probability calibration.", "Review-capacity constraint applies on policy window; future review volumes may exceed it."],
    }
    directory = model_dir()
    directory.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, directory / "fraud_pipeline.joblib")
    (directory / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    test[["Transaction_ID"]].to_csv(directory / "test_ids.csv", index=False)
    # Training reference only; immutable baselines used by monitoring.
    fit[FEATURES].to_csv(directory / "reference.csv", index=False)
    print(json.dumps({"selected": winner["model"], "threshold": bundle.threshold, "test": test_metrics}, indent=2), flush=True)


if __name__ == "__main__":
    train()
