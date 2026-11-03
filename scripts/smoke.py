"""Exercise the real running HTTP service or Vite proxy and save a factual run report."""
import argparse
import json
from datetime import datetime, timezone
import time
import os
import httpx
from src.config import ROOT


def run(base):
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "base_url": base, "checks": []}
    sample = {"Transaction_Date": "2024-02-01T14:30:00", "Transaction_Amount": 100, "Is_International": 0, "Account_Age_Days": 200, "Merchant_Category": "Travel", "Payment_Method": "UPI", "Device_Type": "Mobile", "Location": "Delhi"}
    key = os.getenv("FRAUD_API_KEY")
    with httpx.Client(base_url=base, timeout=20, headers={"X-API-Key": key} if key else {}) as client:
        for path in ["/health", "/model/info", "/model/metrics", "/transactions", "/analytics/overview", "/analytics/fraud", "/monitoring"]:
            start = time.perf_counter()
            response = client.get(path)
            response.raise_for_status()
            report["checks"].append({"endpoint": path, "status": response.status_code, "latency_ms": round((time.perf_counter() - start) * 1000, 2)})
        single = client.post("/predict", json=sample)
        single.raise_for_status()
        batch = client.post("/predict/batch", json={"transactions": [sample, sample]})
        batch.raise_for_status()
        assert len(batch.json()) == 2
        assert abs(single.json()["fraud_probability"] - batch.json()[0]["fraud_probability"]) < 1e-12
        transaction_id = client.get("/transactions?page_size=1").json()["items"][0]["Transaction_ID"]
        assert client.get(f"/transactions/{transaction_id}").status_code == 200
        assert client.get(f"/model/explain/{transaction_id}").json()["method"] == "SHAP"
        assert client.post("/predict", json={**sample, "Transaction_Amount": -1}).status_code == 422
        report["prediction_checks"] = {"single": single.status_code, "batch": batch.status_code, "equivalent": True, "real_shap": single.json()["explanation"]["method"], "invalid_amount_status": 422}
    output = ROOT / "docs/reports/http-smoke.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    run(parser.parse_args().base)
