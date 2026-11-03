# FraudShield demo recording guide

## Verification — 13 October 2026

- 34 Python unit/API/integration tests passed. Four third-party deprecation warnings remain; no test failures.
- TypeScript and Vite production build passed after the overlay fix.
- Live HTTP checks through http://127.0.0.1:5174/api passed for health, model info/metrics, transactions, analytics and monitoring.
- Single and batch predictions agreed; actual SHAP explanations returned; negative amounts received HTTP 422.
- Browser checks passed for transaction investigation, scoring, performance and monitoring. A startup Vite WebSocket error was followed by a successful connection; no subsequent application error was observed in the inspected logs.
- Fixed transaction drawer layering: the sticky header had z-index 30 while the overlay had 25. The overlay now has 50 and renders through a portal into document.body, so tab animation cannot trap it inside a transformed container. Verified the drawer receives pointer hits over the header, its explanation loads, and Escape closes it.
- This checks the exercised paths, not every possible deployment or input. Docker and a new full training run were not tested in this pass.

## Start the application

In one PowerShell terminal:

```powershell
cd C:\Users\harsh\projects\FraudShield-AI
$env:PYTHONPATH=".vendor"
$env:MPLCONFIGDIR="docs/reports/.mplcache"
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

In a second terminal:

```powershell
cd C:\Users\harsh\projects\FraudShield-AI\frontend
npm run dev -- --port 5174 --strictPort
```

If these services are already running, use them instead of starting duplicates. Open http://127.0.0.1:5174/ in your browser. Keep both terminals running.

## Prepare the recording

1. Maximize the browser, use 100% zoom, and keep the analysis cohort at Held-out test.
2. Turn on Do Not Disturb, close unrelated tabs, and check your microphone.
3. Rehearse once. Reload before the final take so the first-scroll animations can play again.
4. On Windows 11, press Win+Shift+R, select the browser area, enable microphone recording if available, and start. Alternatively open Snipping Tool, choose Record, then New. Record a short trial and check the saved audio before the main take.
5. Move the pointer slowly, pause after tab changes, and avoid reading every number aloud.

Microsoft recording instructions: https://support.microsoft.com/en-gb/windows/apps/use-snipping-tool-to-capture-screenshots

## Four-minute recording sequence

| Time | What to show | Narration cue |
| --- | --- | --- |
| 0:00–0:20 | Overview, project name and navigation | “FraudShield combines transaction risk scoring, investigation, model evaluation and data-quality checks in one dashboard.” |
| 0:20–0:50 | Overview cards and charts; scroll gently | “This view uses 745 held-out transactions. The observed fraud rate is 8.5%, and 126 transactions cross the review threshold.” |
| 0:50–1:15 | Analytics; hover over one chart bar | “The analytics view summarizes fraud patterns by merchant, location, payment method and time.” |
| 1:15–2:00 | Transactions; search T102893 and open its ID | “This example receives a 73.4% calibrated fraud probability and is flagged for review. SHAP shows what contributed to the base model score. A review flag is separate from the known label.” |
| 2:00–2:50 | Score transaction; fill the example below; submit | “New transaction details go through the same fitted preprocessing and model pipeline. This example scores 1.8%, below the 24.1% review threshold.” |
| 2:50–3:30 | Model performance, precision/recall and confusion matrix | “The final chronological holdout has PR-AUC 0.305, ROC-AUC 0.838 and recall 55.6%. The model detects 35 of 63 labeled fraud cases and produces 91 false positives, so this is a research prototype with measurable limitations.” |
| 3:30–3:50 | Data quality, missing values and drift tables | “The platform validates source records and compares held-out distributions with the training reference. These are offline checks.” |
| 3:50–4:00 | Return to Overview | “The project demonstrates an end-to-end fraud ML workflow with calibrated predictions, explanations and honest evaluation.” |

## Verified scoring example

| Field | Value |
| --- | --- |
| Transaction timestamp | 1 February 2024, 14:30 |
| Transaction amount | 100 |
| International transaction | No |
| Account age | 200 days |
| Merchant category | Travel |
| Payment method | UPI |
| Device type | Mobile |
| Location | Delhi |

Verified result with the saved model: 1.8% probability, Low display band, Below review threshold. Currency is unspecified dataset units. The timestamp is dataset-local time.

## Finish

Stop the recording, save it as FraudShield-Demo.mp4, trim the start/end, and replay it to check audio, text legibility and transitions. Keep the video around four minutes. Describe the system as an offline research prototype; do not call ROC-AUC “accuracy” or claim production readiness. SHAP contributions explain the estimator before calibration, rather than adding directly to the calibrated probability.
