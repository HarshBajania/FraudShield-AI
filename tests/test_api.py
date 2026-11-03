import numpy as np
import pytest
from src.data import FEATURES


def test_health_metadata_metrics(client):
    assert client.get("/health").json()["model_loaded"]
    info = client.get("/model/info").json()
    assert "Fraudulent" not in info["features"]
    assert "Suspicious_Keyword" not in info["features"]
    assert len(info["split_windows"]) == 5
    m = client.get("/model/metrics").json()["test_metrics"]
    assert sum(map(sum, m["confusion_matrix"])) == m["rows"]
    assert 0 <= m["pr_auc"] <= 1


@pytest.mark.parametrize("amount", [0, 100, 1000000000])
def test_prediction_actual_shap(client, transaction, amount):
    transaction["Transaction_Amount"] = amount
    response = client.post("/predict", json=transaction)
    assert response.status_code == 200
    result = response.json()
    assert 0 <= result["fraud_probability"] <= 1
    assert result["risk_score"] == pytest.approx(100 * result["fraud_probability"])
    assert result["predicted_class"] == int(result["fraud_probability"] >= result["threshold"])
    assert result["explanation"]["method"] == "SHAP"
    assert result["explanation"]["factors"]


def test_shap_additivity_matches_estimator(client, transaction):
    store = client.app.state.service
    import pandas as pd
    frame = pd.DataFrame([transaction])
    e = store.explainer.local(frame)
    raw = store.bundle.pipeline.predict_proba(frame)[0, 1]
    if e["output_space"] == "uncalibrated probability":
        assert e["explained_output"] == pytest.approx(raw, abs=1e-6)
    else:
        assert e["explained_output"] == pytest.approx(np.log(raw / (1 - raw)), abs=1e-6)


def test_batch_single_equivalence_and_missing(client, transaction):
    transaction["Account_Age_Days"] = None
    transaction["Location"] = None
    single = client.post("/predict", json=transaction).json()
    batch = client.post("/predict/batch", json={"transactions": [transaction, transaction]}).json()
    assert len(batch) == 2
    assert batch[0]["fraud_probability"] == pytest.approx(single["fraud_probability"])
    assert single["warnings"] and batch[0]["explanation"] is None


@pytest.mark.parametrize("key,value", [("Transaction_Amount", -1), ("Transaction_Amount", 1e10), ("Transaction_Amount", "nan"), ("Transaction_Date", "not-date"), ("Transaction_Date", "2024-01-01T00:00:00Z"), ("Location", "Atlantis"), ("Is_International", 2), ("Account_Age_Days", -1), ("Fraudulent", 1)])
def test_input_validation(client, transaction, key, value):
    transaction[key] = value
    response = client.post("/predict", json=transaction)
    assert response.status_code == 422
    assert all("input" not in error for error in response.json()["detail"])


def test_malformed_empty_oversized(client):
    for body in [{}, {"transactions": []}, {"transactions": [{}] * 501}]:
        assert client.post("/predict/batch", json=body).status_code == 422
    assert client.post("/predict", content="{bad", headers={"Content-Type": "application/json"}).status_code == 422
    assert client.post("/predict", json={}).status_code == 422
    assert client.post("/predict", content="x", headers={"Content-Length": "2000001"}).status_code == 413


def test_transactions_filters_detail_explanation(client):
    result = client.get("/transactions?page_size=2&sort=risk_score").json()
    assert len(result["items"]) == 2
    assert result["items"][0]["risk_score"] >= result["items"][1]["risk_score"]
    row = result["items"][0]
    response = client.get(f'/transactions/{row["Transaction_ID"]}')
    assert response.status_code == 200
    assert response.json()["prediction"]["fraud_probability"] == pytest.approx(row["fraud_probability"])
    assert "Customer_ID" not in response.json()["transaction"]
    assert client.get(f'/model/explain/{row["Transaction_ID"]}').json()["method"] == "SHAP"
    assert client.get("/transactions/missing").status_code == 404
    assert client.get("/transactions?search=no-such-id").json()["total"] == 0
    assert client.get("/transactions?min_amount=100&max_amount=2").status_code == 422
    assert client.get("/transactions?page=0").status_code == 422
    assert client.get("/transactions?sort=Customer_ID").status_code == 422
    filtered = client.get("/transactions?flagged=true").json()
    assert all(r["predicted_class"] == 1 for r in filtered["items"])


def test_analytics_cohort_consistency(client):
    o = client.get("/analytics/overview").json()
    f = client.get("/analytics/fraud").json()
    assert sum(r["transactions"] for r in f["by_type"]) == o["total_transactions"]
    assert sum(r["count"] for r in f["probability_distribution"]) == o["total_transactions"]
    assert sum(r["fraud"] for r in f["by_location"]) == o["fraudulent_transactions"]
    assert client.get("/analytics/overview?cohort=all").json()["total_transactions"] == 5000
    assert client.get("/monitoring").json()["data_quality"]["rows"] == 5000


def test_auth_safe_logging_headers(client, monkeypatch, transaction):
    monkeypatch.setenv("FRAUD_API_KEY", "test-only-secret")
    assert client.post("/predict", json=transaction).status_code == 401
    response = client.post("/predict", json=transaction, headers={"X-API-Key": "test-only-secret"})
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Request-ID"]


def test_unavailable_model_returns_503(client):
    original = client.app.state.service
    client.app.state.service = None
    try:
        assert client.get("/health").status_code == 503
        assert client.get("/model/info").status_code == 503
    finally:
        client.app.state.service = original
