import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from scripts.train import split_windows
from src.config import dataset_path, training_config
from src.data import FEATURES, load_financial, inference_frame
from src.evaluation import evaluate, select_threshold
from src.features import ENGINEERED, TransactionFeatures, make_pipeline
from src.monitoring import drift_report


@pytest.fixture
def source():
    return load_financial(dataset_path())[0]


def test_date_split_no_overlap(source):
    windows = split_windows(source, training_config()["split_fractions"])
    for first, second in zip(windows[:-1], windows[1:]):
        assert first.Transaction_Date.max().normalize() < second.Transaction_Date.min().normalize()
        assert set(first.Transaction_ID).isdisjoint(second.Transaction_ID)
    assert sum(map(len, windows)) == len(source)


@pytest.mark.parametrize("column,value", [("Transaction_Amount", -1), ("Transaction_Amount", np.inf), ("Location", "UnknownCity"), ("Fraudulent", 3), ("Transaction_Date", "bad"), ("Account_Age_Days", 1.5), ("Is_International", .5)])
def test_source_invalid(tmp_path, column, value):
    frame = pd.read_csv(dataset_path()).head(30).copy()
    frame[column] = frame[column].astype(object)
    frame.loc[0, column] = value
    path = tmp_path / "bad.csv"
    frame.to_csv(path, index=False)
    with pytest.raises((ValueError, TypeError)):
        load_financial(path)


def test_duplicate_and_missing_columns(tmp_path):
    frame = pd.read_csv(dataset_path()).head(30)
    frame.loc[1, "Transaction_ID"] = frame.loc[0, "Transaction_ID"]
    path = tmp_path / "bad.csv"
    frame.to_csv(path, index=False)
    with pytest.raises(ValueError, match="unique"):
        load_financial(path)
    frame.drop(columns="Location").to_csv(path, index=False)
    with pytest.raises(ValueError, match="Missing required"):
        load_financial(path)


def test_features_only_current_transaction(transaction):
    f = inference_frame([transaction])
    transformed = TransactionFeatures().transform(f)
    assert transformed.log_amount.iloc[0] == pytest.approx(np.log1p(100))
    assert transformed.day_of_week.iloc[0] == 3
    assert transformed.weekend.iloc[0] == 0
    assert transformed.hour_sin.iloc[0] == pytest.approx(np.sin(2 * np.pi * 14.5 / 24))
    assert set(ENGINEERED).issubset(transformed.columns)
    assert "Fraudulent" not in transformed and "Suspicious_Keyword" not in transformed


def test_imputation_fitted_only_on_training(source):
    training = source.iloc[:400].copy()
    pipeline = make_pipeline(LogisticRegression(max_iter=1000)).fit(training[FEATURES], training.Fraudulent)
    before = pipeline.named_steps["preprocess"].named_transformers_["numeric"].named_steps["impute"].statistics_.copy()
    missing = training[FEATURES].iloc[:2].copy()
    missing["Account_Age_Days"] = np.nan
    missing["Location"] = np.nan
    missing["Transaction_Amount"] = 1e9
    assert np.isfinite(pipeline.predict_proba(missing)).all()
    np.testing.assert_array_equal(before, pipeline.named_steps["preprocess"].named_transformers_["numeric"].named_steps["impute"].statistics_)
    assert before[0] == pytest.approx(training.Transaction_Amount.median())


def test_cost_policy_capacity():
    config = training_config()
    y, p, amounts = np.array([0, 0, 1, 1, 0]), np.array([.1, .2, .8, .9, .3]), np.array([10, 10, 100, 200, 10])
    threshold, rows = select_threshold(y, p, amounts, config)
    result = evaluate(y, p, amounts, threshold, config)
    assert result["review_rate"] <= config["review_capacity_fraction"]
    assert result["confusion_matrix"] == [[3, 0], [1, 1]]
    assert result["estimated_cost"] == 105
    assert result["fraud_amount_captured"] == 200


def test_equal_scores_allow_no_review():
    threshold, _ = select_threshold(np.array([0, 1]), np.ones(2), np.array([1., 2.]), training_config())
    assert threshold > 1


def test_monitor_detects_large_shift(source):
    shifted = source.copy()
    shifted["Transaction_Amount"] += 10000
    shifted["Location"] = "Delhi"
    report = drift_report(source, shifted)
    assert report["numeric"]["Transaction_Amount"]["warning"]
    assert report["categorical"]["Location"]["warning"]
