"""Strict source and inference contracts, with explicit missing-data handling."""
from datetime import datetime
from typing import Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator
from src.config import training_config

MAX_AMOUNT = training_config()["max_amount"]

CATEGORIES = {
    "Merchant_Category": ["Travel", "Utilities", "Entertainment", "Health", "Fashion", "Grocery", "Food", "Electronics"],
    "Payment_Method": ["PayPal", "Debit Card", "NetBanking", "Credit Card", "UPI"],
    "Device_Type": ["POS", "Mobile", "Desktop"],
    "Location": ["Bengaluru", "Kolkata", "Mumbai", "Delhi", "Chennai", "Pune", "Hyderabad"],
}
NUMERIC = ["Transaction_Amount", "Is_International", "Account_Age_Days"]
FEATURES = ["Transaction_Date", *NUMERIC, *CATEGORIES]
EXCLUDED = ["Transaction_ID", "Customer_ID", "Fraudulent", "Suspicious_Keyword", "Previous_Transactions", "Average_Spend"]


class Transaction(BaseModel):
    """No label, customer identifier or unverified historical signals enter inference."""
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    Transaction_Date: datetime
    Transaction_Amount: float = Field(ge=0, le=MAX_AMOUNT)
    Is_International: Literal[0, 1]
    Account_Age_Days: int | None = Field(default=None, ge=0, le=100000)
    Merchant_Category: Literal["Travel", "Utilities", "Entertainment", "Health", "Fashion", "Grocery", "Food", "Electronics"] | None = None
    Payment_Method: Literal["PayPal", "Debit Card", "NetBanking", "Credit Card", "UPI"] | None = None
    Device_Type: Literal["POS", "Mobile", "Desktop"] | None = None
    Location: Literal["Bengaluru", "Kolkata", "Mumbai", "Delhi", "Chennai", "Pune", "Hyderabad"] | None = None

    @field_validator("Transaction_Date")
    @classmethod
    def local_time(cls, value: datetime) -> datetime:
        if value.tzinfo is not None:
            raise ValueError("Use a timezone-naive dataset-local timestamp; source timezone is unknown")
        if not 2000 <= value.year <= 2100:
            raise ValueError("Date year must be between 2000 and 2100")
        return value


def load_financial(path) -> tuple[pd.DataFrame, dict]:
    frame = pd.read_csv(path)
    required = set(FEATURES + ["Transaction_ID", "Fraudulent"])
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("Dataset is empty")
    if frame.Transaction_ID.isna().any() or frame.Transaction_ID.duplicated().any():
        raise ValueError("Transaction identifiers must be present and unique")
    if not frame.Fraudulent.isin([0, 1]).all() or frame.Fraudulent.nunique() != 2:
        raise ValueError("Labels must contain both 0 and 1")
    frame["Transaction_Date"] = pd.to_datetime(frame.Transaction_Date, format="%d-%m-%Y %H:%M", errors="raise")
    if not frame.Transaction_Date.dt.year.between(2000, 2100).all():
        raise ValueError("Timestamp outside supported range")
    for col in NUMERIC:
        frame[col] = pd.to_numeric(frame[col], errors="raise")
        observed = frame[col].dropna()
        maximum = MAX_AMOUNT if col == "Transaction_Amount" else (1 if col == "Is_International" else 100000)
        if not np.isfinite(observed).all() or (observed < 0).any() or (observed > maximum).any():
            raise ValueError(f"Invalid numeric values in {col}")
    if frame.Transaction_Amount.isna().any() or frame.Is_International.isna().any():
        raise ValueError("Amount and international indicator are required")
    if not frame.Is_International.isin([0, 1]).all():
        raise ValueError("International indicator must be binary")
    if (frame.Account_Age_Days.dropna() % 1 != 0).any():
        raise ValueError("Account age must contain whole days")
    for col, allowed in CATEGORIES.items():
        if not frame[col].dropna().isin(allowed).all():
            raise ValueError(f"Unexpected category in {col}")
    report = {
        "rows": len(frame), "fraud_count": int(frame.Fraudulent.sum()),
        "fraud_rate": float(frame.Fraudulent.mean()),
        "missing": frame.isna().sum().to_dict(), "duplicate_rows": int(frame.duplicated().sum()),
        "zero_amounts": int((frame.Transaction_Amount == 0).sum()),
        "amount_outliers_iqr": int((frame.Transaction_Amount > frame.Transaction_Amount.quantile(.75) + 1.5 * (frame.Transaction_Amount.quantile(.75) - frame.Transaction_Amount.quantile(.25))).sum()),
        "excluded_features": EXCLUDED,
        "availability_warning": "Historical spend/count and Suspicious_Keyword excluded: point-in-time provenance unavailable. Account age and international status assumed available at authorization.",
    }
    return frame.sort_values("Transaction_Date", kind="stable").reset_index(drop=True), report


def inference_frame(records: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(records, columns=FEATURES).replace({None: np.nan})
