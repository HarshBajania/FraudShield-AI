"""Only transaction-local features; fitted encoders and imputers live in the pipeline."""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.data import CATEGORIES, NUMERIC

ENGINEERED = ["log_amount", "hour_sin", "hour_cos", "day_of_week", "weekend"]


class TransactionFeatures(TransformerMixin, BaseEstimator):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        frame = X.copy()
        date = pd.to_datetime(frame["Transaction_Date"])
        frame["log_amount"] = np.log1p(frame.Transaction_Amount)
        hour = date.dt.hour + date.dt.minute / 60
        frame["hour_sin"] = np.sin(2 * np.pi * hour / 24)
        frame["hour_cos"] = np.cos(2 * np.pi * hour / 24)
        frame["day_of_week"] = date.dt.dayofweek
        frame["weekend"] = (date.dt.dayofweek >= 5).astype(int)
        return frame[NUMERIC + ENGINEERED + list(CATEGORIES)]


def make_pipeline(estimator) -> Pipeline:
    numeric = Pipeline([("impute", SimpleImputer(strategy="median", add_indicator=True)), ("scale", StandardScaler())])
    categorical = Pipeline([("impute", SimpleImputer(strategy="constant", fill_value="Missing")), ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False))])
    preprocess = ColumnTransformer([("numeric", numeric, NUMERIC + ENGINEERED), ("category", categorical, list(CATEGORIES))], verbose_feature_names_out=False)
    return Pipeline([("features", TransactionFeatures()), ("preprocess", preprocess), ("model", estimator)])
