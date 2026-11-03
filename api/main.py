"""FastAPI entrypoint with validated inputs, safe failures and structured logging."""
from contextlib import asynccontextmanager
import json
import logging
import os
import secrets
import time
import uuid
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.schemas import BatchRequest, Prediction
from api.service import FraudService
from src.data import CATEGORIES, FEATURES, MAX_AMOUNT, Transaction

logger = logging.getLogger("fraudshield")
logging.basicConfig(level=os.getenv("FRAUD_LOG_LEVEL", "INFO"), format="%(message)s")


@asynccontextmanager
async def lifespan(app):
    app.state.service = None
    app.state.load_error = None
    try:
        app.state.service = FraudService()
        logger.info(json.dumps({"event": "model_loaded", "model": app.state.service.metadata["model_name"]}))
    except Exception as error:
        app.state.load_error = type(error).__name__
        logger.error(json.dumps({"event": "model_load_failed", "error_type": type(error).__name__}))
    yield


app = FastAPI(title="Financial Fraud Detection & Risk Analytics Platform", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("FRAUD_CORS", "http://localhost:5173,http://localhost:8080").split(","), allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Content-Type", "X-API-Key"])


def authorize(request: Request):
    configured = os.getenv("FRAUD_API_KEY")
    if configured and not secrets.compare_digest(configured, request.headers.get("X-API-Key", "")):
        raise HTTPException(401, "Valid API key required")


def service(request: Request, _: None = Depends(authorize)) -> FraudService:
    result = getattr(request.app.state, "service", None)
    if result is None:
        raise HTTPException(503, "Model unavailable. Run python -m scripts.train and restart the API.")
    return result


@app.middleware("http")
async def operational_logging(request, call_next):
    start, request_id = time.perf_counter(), uuid.uuid4().hex
    # Request bodies and query values are deliberately never logged.
    length = request.headers.get("content-length")
    if length and (not length.isdigit() or int(length) > 2_000_000):
        return JSONResponse(status_code=413, content={"detail": "Request body exceeds limit"})
    try:
        response = await call_next(request)
    except Exception as error:
        logger.error(json.dumps({"event": "request_error", "request_id": request_id, "error_type": type(error).__name__}))
        response = JSONResponse(status_code=500, content={"detail": "Internal service error", "request_id": request_id})
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    route = request.scope.get("route")
    logger.info(json.dumps({"event": "request", "request_id": request_id, "route": getattr(route, "path", "unmatched"), "method": request.method, "status": response.status_code, "duration_ms": round((time.perf_counter() - start) * 1000, 2)}))
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    logger.warning(json.dumps({"event": "validation_failed", "error_count": len(exc.errors())}))
    return JSONResponse(status_code=422, content={"detail": [{"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]} for e in exc.errors()]})


@app.get("/health")
def health(request: Request):
    ready = getattr(request.app.state, "service", None) is not None
    return JSONResponse(status_code=200 if ready else 503, content={"status": "ready" if ready else "degraded", "model_loaded": ready, "environment": os.getenv("FRAUD_ENV", "development")})


@app.get("/model/info")
def model_info(store=Depends(service)):
    keys = ["model_name", "model_version", "training_date", "dataset_version", "dataset_file", "features", "split_windows", "libraries", "selection_reason", "limitations", "training_config", "selected_parameters"]
    return {**{k: store.metadata[k] for k in keys}, "threshold": store.threshold, "trained_threshold": store.bundle.threshold, "risk_boundaries": store.boundaries, "categories": CATEGORIES, "auth_enabled": bool(os.getenv("FRAUD_API_KEY"))}


@app.post("/predict", response_model=Prediction)
def predict(transaction: Transaction, store=Depends(service)):
    return store.predict([transaction])[0]


@app.post("/predict/batch", response_model=list[Prediction])
def predict_batch(body: BatchRequest, explain: bool = False, store=Depends(service)):
    return store.predict(body.transactions, explain=explain)


@app.get("/transactions")
def transactions(search: str = Query("", max_length=100), location: str | None = None,
                 merchant: str | None = None, risk: Literal["Low", "Moderate", "High", "Critical"] | None = None,
                 flagged: bool | None = None, min_amount: float = Query(0, ge=0), max_amount: float = Query(MAX_AMOUNT, ge=0, le=MAX_AMOUNT),
                 cohort: Literal["all", "test", "development"] = "test",
                 sort: Literal["risk_score", "Transaction_Amount", "Transaction_Date"] = "risk_score",
                 descending: bool = True, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), store=Depends(service)):
    if min_amount > max_amount:
        raise HTTPException(422, "Minimum amount exceeds maximum")
    frame = store.cohort(cohort)
    if search:
        frame = frame[frame.Transaction_ID.str.contains(search, case=False, regex=False)]
    for column, value in [("Location", location), ("Merchant_Category", merchant), ("risk_category", risk)]:
        if value is not None:
            frame = frame[frame[column] == value]
    if flagged is not None:
        frame = frame[frame.predicted_class == int(flagged)]
    frame = frame[frame.Transaction_Amount.between(min_amount, max_amount)].sort_values(sort, ascending=not descending, kind="stable")
    start = (page - 1) * page_size
    return {"items": store.serialize(frame.iloc[start:start + page_size]), "total": len(frame), "page": page, "page_size": page_size, "cohort": cohort}


@app.get("/transactions/{transaction_id}")
def transaction_detail(transaction_id: str, store=Depends(service)):
    row = store.record(transaction_id)
    if row is None:
        raise HTTPException(404, "Transaction not found")
    record = Transaction.model_validate(row[FEATURES].where(row[FEATURES].notna(), None).to_dict())
    return {"transaction": store.serialize(store.frame[store.frame.Transaction_ID == transaction_id])[0], "prediction": store.predict([record])[0]}


@app.get("/model/explain/{transaction_id}")
def explain(transaction_id: str, store=Depends(service)):
    return transaction_detail(transaction_id, store)["prediction"]["explanation"]


@app.get("/analytics/overview")
def overview(cohort: Literal["all", "test", "development"] = "test", store=Depends(service)):
    return store.overview(cohort)


@app.get("/analytics/fraud")
def fraud_analytics(cohort: Literal["all", "test", "development"] = "test", store=Depends(service)):
    return store.analytics(cohort)


@app.get("/model/metrics")
def metrics(store=Depends(service)):
    keys = ["test_metrics", "test_uncertainty", "constant_baseline_test", "model_comparison", "curves", "threshold_analysis", "global_explanations"]
    return {**{k: store.metadata[k] for k in keys}, "note": "Test metrics use the frozen trained threshold, even when the serving policy is overridden."}


@app.get("/monitoring")
def monitoring(store=Depends(service)):
    return {"data_quality": store.quality, "train_test_drift": store.metadata["drift"], "model_version": store.metadata["model_version"], "note": "Offline train/test drift and data validation; no connected live transaction stream or delayed labels."}
