# Actual validation report — 7 October 2026

All numbers below are based on commands and browser interactions actually executed in this workspace. This report separates verified behavior from unavailable tooling.

| Check | Actual outcome |
|---|---|
| Financial source validation | 5,000 rows; 482 fraud labels; no missing values or duplicate IDs; 2 zero amounts; 240 IQR upper outliers |
| Primary training | Completed 10 hyperparameter runs across 5 candidate variants; calibrated each on independent chronological data; selected weighted forest by policy cost |
| Primary holdout inference | 745 rows; PR-AUC 0.304957; ROC-AUC 0.838128; confusion matrix [[591,91],[28,35]] |
| Test PR-AUC uncertainty | Seeded 300-resample bootstrap 95% interval [0.226430,0.417041] |
| Credit benchmark and EDA | Completed logistic/forest/histogram-boosting validation comparison and winner-only test; actual weak holdout results preserved in audit JSON |
| Backend unit / integration / API suite | 34 passing behavioral tests in the final completed run; actual model and SHAP, no mocked probabilities |
| API startup | Uvicorn started and model loaded on loopback port 8000 |
| Real HTTP smoke | All 7 GET endpoints checked returned 200; single/batch scoring returned 200, agreed numerically, and invalid amount returned 422; rerun successfully through the Vite /api proxy |
| Frontend | TypeScript compile and Vite production build passed; chart bundle separated to remove the original >500KB chunk warning |
| Dependency audit | npm install reported 0 vulnerabilities in the installed frontend dependency set at run time |
| Browser — overview | Actual model-connected overview with 745 held-out rows, 8.5% observed fraud, 126 flags and dataset-unit values |
| Browser — investigation | Loaded scored ledger and real T102893 explanation: calibrated probability 73.4%; base-estimator SHAP probability reconstructed separately |
| Browser — empty search | Nonexistent literal transaction search showed the expected empty state |
| Browser — keyboard and pagination | Tab remains within the investigation drawer; Escape closes it; next-page navigation showed page 2 of 50 |
| Browser — single form | Entered actual valid schema example; returned 1.8% calibrated probability and real SHAP factors |
| Browser — batch | Two entered schema examples produced 4.4% and 67.3% calibrated probabilities with distinct review decisions |
| Browser — model evidence | Actual comparison, confusion matrix, holdout curves and business scenario visible |
| Browser — monitoring | Numerical drift and chronological lineage loaded; no sampled browser error logs |
| Responsive tablet | 768×1024 viewport; document width 753px with scrollbar, no page-level horizontal overflow; labels improved to horizontal bars |
| Visual artifacts | EDA image inspected; final dashboard screenshot saved to docs/reports/dashboard.jpg |
| Notebook portability | Preserved original notebook input paths made portable; all four notebook code sections passed syntax parsing; optional Jupyter notebooks were not executed in a kernel |
| Docker | Command unavailable on this machine; container build/runtime not verified |

The restricted Windows sandbox blocked pytest's temporary directories and the socket used by the Python async event loop. Tests and the working server were rerun with authorized access. API tests exposed two overly broad assertions about the literal word “input”; those were fixed to assert that submitted input fields are absent from validation errors. The final suite passed. The earlier incompatible globally installed FastAPI/Starlette stack was replaced with project-local compatible dependencies, recorded in requirements-lock.txt.

The original large frontend chunk warning was addressed by isolating Recharts. Browser inspection found crowded categorical labels at tablet size and retained scroll position on navigation; charts were changed to horizontal bars, chart animations were disabled, and section navigation resets scrolling. Vite configuration edits briefly restarted the server; a fresh final browser tab was verified afterward.

The exact local tested environment used Python 3.14.4, scikit-learn 1.9.1, pandas 3.0.6 and NumPy 2.5.3. Upstream Starlette test-client and SHAP/Matplotlib deprecation warnings remain informational; no test failed on them. Fresh installations and Docker train their own artifacts; do not load cross-version or untrusted joblib files.

Reproduce:

```powershell
$env:PYTHONPATH='.vendor' # Only for the already provisioned restricted workspace
$env:MPLCONFIGDIR='docs/reports/.mplcache'
python -m pytest -q
python -m scripts.smoke --base http://127.0.0.1:8000
cd frontend
npm run build
```

The running dashboard used port 5174 during browser verification because an earlier sandboxed server occupied 5173. Ordinary `npm run dev` uses 5173. Both source files remain preserved; no fabricated outcomes or metric fixtures are used.

## Navigation and visual revision

The subsequent UI revision passed TypeScript and the Vite production build. Browser checks confirmed the desktop navigation is 60px collapsed and 236px when hovered, expands for visible keyboard focus, and collapses when the pointer leaves. The rail expands over the content without resizing charts. At 390×844, the menu toggle opened navigation and selecting Analytics closed it; document width was 375px including the scrollbar, with no page overflow. Branding now uses a custom inline vector monogram and wordmark; typography uses system fonts. The decorative workspace card, analyst profile and repeated slogans were removed. Updated preview: `docs/reports/dashboard-redesign.jpg`.
