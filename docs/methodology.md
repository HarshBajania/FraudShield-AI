# Experiment protocol and interpretation

The original notebook contains descriptive analysis and duplicate checks; it has no trained estimator, split protocol, preprocessing pipeline or model results to reuse. It remains preserved, with its machine-specific input paths made portable. The new notebooks read the shared code and actual experiment reports rather than implementing parallel inference logic.

## Leakage controls

Sort financial transactions by explicitly parsed event time. Divide whole calendar days into five disjoint windows. Configured fractions are fractions of unique days, so row fractions differ slightly. Current actual windows contain 2,457 fit, 764 tuning, 535 calibration, 499 policy and 745 test records. All labels are present in each window. Fail if this condition cannot be met.

Only the fit window trains feature imputers, standardization, one-hot category vocabularies and estimators. The tuning window selects each family's hyperparameters by average precision. The calibration window fits a sigmoid on clipped raw-probability log odds with ordinary, unweighted logistic loss. The policy window sets each model's cost-optimal review threshold under a capacity limit and selects the family by scenario cost. Only then is the selected pipeline evaluated on the test window. The final model is not refitted on test or selection data. This uses data conservatively and leaves relatively small calibration/selection windows. Use rolling-origin experiments with nested calibration for stronger evidence on a larger dataset.

Repeated customers can appear across chronological windows. Identifiers are excluded from the features, but correlated recurring behavior could still affect results. These results measure later transactions in this source, not generalization to unseen customers. Add a customer-disjoint sensitivity experiment if new-customer deployment is intended.

## Models and imbalance

Logistic regression provides an interpretable low-variance baseline; random forest tests nonlinear interactions; gradient boosting tests additive nonlinear structure. Logistic regularization C values are 0.1 and 1. Forest max depths are 5 and 10 with minimum leaf size 12 and 150 estimators. Boosted trees use depth 1 or 2, learning rate 0.05, 100 trees and minimum leaf size 15. Unweighted and balanced variants of logistic regression and forest isolate the effect of class weights. All randomness uses seed 42.

SMOTE is not used: mixed categorical inputs and unknown synthetic-source semantics do not justify fabricated neighboring transactions. Tree weighting and threshold policy are tested directly. Weighted raw probabilities need not reflect prevalence, so all candidates receive independent sigmoid calibration. XGBoost/LightGBM are omitted because the supplied dataset has only 5,000 records and the existing tree families already provide a defensible comparison without extra dependencies. Neither weights nor calibration are claimed universally best.

Policy-window comparisons and tuning parameters are stored in `models/metadata.json`. The selected weighted random forest has the lowest configured policy cost. This selection is sensitive to assumed investigation cost, false-positive friction, loss multiplier and review capacity; change them in `configs/training.json` and rerun the full protocol, not a test-driven threshold search.

## Features

Raw transaction amount, international indicator, account age, merchant category, payment method, device type and location are eligible inputs. Engineered features are log1p(amount), sine/cosine of fractional local hour, weekday and weekend indicator. These require only the current transaction. Raw datetime is removed after engineering. Customer and merchant frequency, amount relative to past spend, velocity, calendar month and unique identifiers are deliberately absent from the served model. Historical features can be added only after point-in-time source contracts and online state are available.

One-hot encoders ignore unknown categories defensively, but the source and public API reject unsupported categories. Missing optional categorical values use an explicit token. Optional account age uses a fit-window median. Scaling is harmless for trees and allows a consistent shared preprocessing path for logistic regression. No preprocessing is hand-reimplemented in the API.

## Metric definitions

PR-AUC here means scikit-learn **average precision**, not trapezoidal area under the plotted curve. ROC-AUC, precision, recall, F1, false-positive/negative rates, confusion matrix and Brier score are measured on holdout. Fraud capture rate equals recall; amount capture rate measures fraud value captured rather than transaction count. Precision@K and Recall@K rank calibrated scores with stable tie handling; K is ceil(test rows × review-capacity fraction).

Confusion matrices use rows `[actual legitimate, actual fraud]` and columns `[predicted legitimate, predicted fraud]`. Estimated scenario cost = review count × investigation cost + false positives × false-positive friction + missed fraud amount × loss multiplier. Captured value assumes review prevents the entire configured loss; actual prevention rates and recovery costs are unknown. Expected exposure = sum(amount × probability), an unvalidated expectation under model probabilities. Currency is undocumented.

The threshold search includes a uniform grid, each policy score, and a no-review option greater than one. Capacity is a hard constraint on the policy sample; it is not guaranteed under distribution shift. If all probabilities are equal, reviewing nobody may be the only feasible policy. Serving threshold overrides are explicit; historical test metrics always use the frozen trained threshold.

The test PR-AUC confidence interval uses 300 seeded bootstrap resamples of held-out predictions and labels, skipping single-class samples. It captures sample uncertainty for this fixed trained model, not training variability or external validity.

## Explainability

Use real TreeSHAP for the selected forest. For logistic candidates the supported path uses LinearSHAP; boosted trees use TreeSHAP in raw log-odds space. Forest contributions plus the expected value reconstruct the **uncalibrated base estimator probability**; sigmoid calibration then maps that output to the displayed probability. Local explanations show the top eight transformed input terms, not a fabricated statement about why fraud happened. Global importance is mean absolute SHAP on up to 200 time-ordered test records. Values describe associations, not causation; calibration effects and correlated features complicate interpretation. Additivity is checked against the actual estimator in integration tests.

## Monitoring and provenance

Offline source validation and fit/test drift diagnostics use numerical KS statistics and categorical total-variation distance. The diagnostic warning threshold of 0.15 is an adjustable engineering convention, not a calibrated fraud alarm. No live traffic stream, investigation disposition, labels, performance alerts or concept-drift claims are simulated. Library versions, dataset hash, training timestamp, feature list, cost config, split boundaries and actual outputs are included in the saved metadata.

The independent credit benchmark uses date-separated 60/20/20 windows, numeric amount/log amount/weekday/month and transaction-type/location encoding, with IDs excluded. Select between weighted logistic regression, weighted forest and histogram gradient boosting on validation PR-AUC, then test the winner once. Its actual holdout PR-AUC is below prevalence and ROC-AUC below 0.5. This is evidence of weak predictive utility in the tested protocol, not proof that fraud is inherently unpredictable or that labels were randomly generated.
