# API contract

Interactive OpenAPI: `http://localhost:8000/docs`. Backend binds loopback by default in local instructions. If `FRAUD_API_KEY` is set, every data/model/prediction endpoint requires `X-API-Key`; health and documentation are public. The dashboard stores the optional key only in session storage. This is a portfolio access gate, not enterprise identity infrastructure.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | /health | Readiness; returns 503 when model failed to load |
| GET | /model/info | Model lineage, categories, active/frozen policies |
| GET | /model/metrics | Frozen test evidence, policy comparison, curves, SHAP importance |
| POST | /predict | Calibrated probability, score, decision, SHAP explanation |
| POST | /predict/batch | 1–500 rows; `?explain=true` optionally enables SHAP |
| GET | /transactions | Filter, search, sort, pagination; test cohort by default |
| GET | /transactions/{transaction_id} | Details and explanation; 404 if absent |
| GET | /model/explain/{transaction_id} | Base-estimator SHAP explanation |
| GET | /analytics/overview | Aggregate values and recent labeled fraud |
| GET | /analytics/fraud | Monthly, location, merchant, payment, amount and score distributions |
| GET | /monitoring | Offline quality and train/test drift diagnostics |

Prediction example:

```json
{
  "Transaction_Date": "2024-02-01T14:30:00",
  "Transaction_Amount": 100,
  "Is_International": 0,
  "Account_Age_Days": 200,
  "Merchant_Category": "Travel",
  "Payment_Method": "UPI",
  "Device_Type": "Mobile",
  "Location": "Delhi"
}
```

Amount, date and international indicator are required. Account age and categories are optional/null and use the fitted imputation path. The response includes probability [0,1], score [0,100], predicted class, category, threshold, model version, warnings and explanation. Extra fields are forbidden, including target, customer ID and suspicious keyword. Timestamps are ISO local datetimes without timezone offsets; numerical infinities and NaNs are forbidden. Allowed categories are exposed in model info.

Batch envelope: `{"transactions": [<transaction>, ...]}`. Defaults to no SHAP to keep latency bounded; response is an ordered prediction array. Empty and oversized lists fail with 422. No uploads, external artifact URLs, pickles, custom file paths or arbitrary models are accepted.

Transactions query: `search` is a literal substring of transaction ID (not regex); `location`, `merchant`, `risk`, `flagged`, `min_amount`, `max_amount`; `cohort=test|all|development`; `sort=risk_score|Transaction_Amount|Transaction_Date`; `descending=true|false`; `page>=1`, `page_size=1..100`. Known outcome is clearly separated from model decision. Customer identifiers are omitted. All/development cohorts include previously seen records and are unsuitable for unbiased model assessment.

Errors use safe JSON details and HTTP 401/404/413/422/503/500. Validation responses omit submitted input values. Each response has an `X-Request-ID`; application logs contain route templates, method, status and latency rather than bodies, search strings, keys or transaction IDs. CORS uses an explicit allowlist. Uvicorn access logs are disabled in recommended commands to avoid raw-path/query logging.

Deployment boundary: local portfolio demonstration. Before public production exposure add reverse-proxy request limits and timeouts, TLS, authentication/authorization, rate limiting, secret management, persistent storage and delayed-label monitoring. The in-memory dataset is a bounded read-only offline store; new predictions are not persisted or added to the analytical cohort.
