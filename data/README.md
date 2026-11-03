# Dataset contracts

Both original CSV files are preserved under `raw/`. They are never pooled.

| Dataset | Rows | Target | Observed fraud | Use |
|---|---:|---|---:|---|
| financial_fraud_detection_dataset.csv | 5,000 | Fraudulent | 482 (9.64%) | Main modeling, API, investigation dashboard |
| credit_card_fraud_dataset.csv | 100,000 | IsFraud | 1,000 (1%) | Independent weak-signal benchmark |

These counts come from the supplied files. No source URL, license, currency, timezone, data-generation process, or definition of a confirmed fraud label was supplied. Do not claim real banking provenance, real financial losses, or unrestricted redistribution rights. Amounts are displayed as **dataset units**.

Financial schema: transaction and customer IDs; day-first local datetime; transaction amount; merchant category; payment method; device type; location; international indicator; previous transaction count; average spend; account age in days; suspicious keyword; binary target. Credit schema: transaction ID; day-first date; amount; merchant ID; transaction type; location; binary target.

The platform rejects nonfinite/negative amounts, unsupported dates, duplicate IDs, invalid target values and unexpected categories. Zero amounts are allowed but counted. Optional account age and categorical fields can be missing; numeric medians and missing-category tokens are fitted inside the training pipeline. The current files have no missing values or duplicate rows. IQR outliers are reported and retained; large values may be legitimate fraud evidence.

`Suspicious_Keyword` has a strong target association but unknown origin; `Average_Spend` and `Previous_Transactions` lack point-in-time provenance. All three are excluded from the main model. IDs and target are excluded too. Account age and international status are assumed known at transaction authorization; confirm this before real deployment. No inferred customer history, future aggregates or velocity features are manufactured.

Dates are parsed with explicit `%d-%m-%Y %H:%M` and `%d-%m-%Y` formats. API dates use timezone-naive ISO 8601 to match this undocumented local-time convention. A future deployment needs an explicit timezone contract.

Run `python -m scripts.audit` to regenerate the quality audit and analytical figures. Model training records a SHA-256 file fingerprint. The API refuses to serve a different data version without retraining. Processed data is not required; fitted preprocessing is persisted with the estimator.
