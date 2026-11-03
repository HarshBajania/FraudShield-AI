"""Independent dataset audit, meaningful EDA plots and separate credit benchmark."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.config import ROOT, dataset_path
from src.data import load_financial


def run():
    out = ROOT / "docs" / "reports"
    out.mkdir(parents=True, exist_ok=True)
    frame, quality = load_financial(dataset_path())
    credit = pd.read_csv(ROOT / "data/raw/credit_card_fraud_dataset.csv")
    credit["date"] = pd.to_datetime(credit.TransactionDate, format="%d-%m-%Y")
    if credit.TransactionID.duplicated().any() or credit.isna().any().any() or not credit.IsFraud.isin([0, 1]).all() or (credit.Amount < 0).any():
        raise ValueError("Invalid credit dataset")
    credit = credit.sort_values("date", kind="stable")
    unique = np.sort(credit.date.unique())
    a, b = unique[int(.6 * len(unique))], unique[int(.8 * len(unique))]
    train, validation, test = credit[credit.date < a].copy(), credit[(credit.date >= a) & (credit.date < b)].copy(), credit[credit.date >= b].copy()
    for part in [train, validation, test]:
        part["log_amount"] = np.log1p(part.Amount)
        part["weekday"] = part.date.dt.dayofweek
        part["month"] = part.date.dt.month
    numeric, categorical = ["Amount", "log_amount", "weekday", "month"], ["TransactionType", "Location"]
    candidates = {
        "logistic": LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
        "random_forest": RandomForestClassifier(n_estimators=80, max_depth=6, min_samples_leaf=30, class_weight="balanced", random_state=42, n_jobs=-1),
        "hist_gradient_boosting": HistGradientBoostingClassifier(max_iter=80, max_leaf_nodes=10, random_state=42),
    }
    results, fitted = [], {}
    for name, estimator in candidates.items():
        prep = ColumnTransformer([("num", make_pipeline(SimpleImputer(), StandardScaler()), numeric), ("cat", OneHotEncoder(sparse_output=False, handle_unknown="ignore"), categorical)])
        pipeline = make_pipeline(prep, estimator).fit(train[numeric + categorical], train.IsFraud)
        p = pipeline.predict_proba(validation[numeric + categorical])[:, 1]
        results.append({"model": name, "validation_pr_auc": float(average_precision_score(validation.IsFraud, p))})
        fitted[name] = pipeline
    selected = max(results, key=lambda x: x["validation_pr_auc"])["model"]
    p = fitted[selected].predict_proba(test[numeric + categorical])[:, 1]
    credit_report = {"rows": len(credit), "fraud_count": int(credit.IsFraud.sum()), "fraud_rate": float(credit.IsFraud.mean()), "missing": credit.isna().sum().to_dict(), "duplicates": int(credit.duplicated().sum()), "excluded": ["TransactionID", "MerchantID"], "validation_comparison": results, "selected": selected, "test_pr_auc": float(average_precision_score(test.IsFraud, p)), "test_roc_auc": float(roc_auc_score(test.IsFraud, p)), "test_prevalence": float(test.IsFraud.mean()), "split_rows": [len(train), len(validation), len(test)], "note": "Independent benchmark, not pooled with financial dataset. Merchant ID excluded because identifier semantics are undocumented."}
    audit = {"financial": quality, "credit": credit_report, "suspicious_keyword_label_crosstab": pd.crosstab(frame.Suspicious_Keyword, frame.Fraudulent).to_dict(), "numeric_target_correlations": frame.select_dtypes("number").corr()["Fraudulent"].to_dict(), "provenance": "No source license, origin, currency, timezone or label-generation documentation supplied; do not assume real banking data."}
    (out / "audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 10, "figure.facecolor": "#faf8f4", "axes.facecolor": "#faf8f4"})
    fig, axes = plt.subplots(2, 3, figsize=(16, 9), layout="constrained")
    counts = frame.Fraudulent.value_counts().sort_index()
    axes[0, 0].bar(["Legitimate", "Fraud"], counts, color=["#59675e", "#913b48"])
    axes[0, 0].set_title("Label imbalance: use PR-AUC, not accuracy")
    for label, color in [(0, "#59675e"), (1, "#913b48")]:
        axes[0, 1].hist(frame.loc[frame.Fraudulent == label, "Transaction_Amount"], bins=35, density=True, histtype="step", color=color, label="Fraud" if label else "Legitimate")
    axes[0, 1].legend(); axes[0, 1].set_title("Does transaction value separate the labels?")
    for ax, col in [(axes[0, 2], "Merchant_Category"), (axes[1, 0], "Location")]:
        groups = frame.groupby(col).Fraudulent.agg(["mean", "count"])
        ax.barh(groups.index, groups["mean"] * 100, color="#913b48")
        ax.set_xlabel("Observed fraud rate (%)"); ax.set_title(f"Fraud rate by {col.replace('_', ' ').lower()}")
    monthly = frame.set_index("Transaction_Date").resample("MS").Fraudulent.agg(["mean", "count"])
    axes[1, 1].plot(monthly.index, monthly["mean"] * 100, color="#913b48")
    axes[1, 1].tick_params(axis="x", rotation=35); axes[1, 1].set_title("Monthly fraud prevalence (edge months may be partial)")
    corr = frame.select_dtypes("number").corr()["Fraudulent"].drop("Fraudulent")
    axes[1, 2].barh(corr.index, corr, color="#65615b"); axes[1, 2].set_title("Numeric associations: weak amount signal")
    fig.savefig(out / "eda.png", dpi=150)
    plt.close(fig)
    print(json.dumps(credit_report, indent=2))


if __name__ == "__main__":
    run()
