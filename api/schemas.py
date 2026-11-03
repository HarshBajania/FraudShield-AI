"""Typed API responses and bounded request envelopes."""
from pydantic import BaseModel, ConfigDict, Field
from src.data import Transaction


class BatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    transactions: list[Transaction] = Field(min_length=1, max_length=500)


class Factor(BaseModel):
    feature: str
    contribution: float
    transformed_value: float


class Explanation(BaseModel):
    method: str
    output_space: str
    note: str
    base_value: float
    explained_output: float
    factors: list[Factor]


class Prediction(BaseModel):
    fraud_probability: float
    risk_score: float
    predicted_class: int
    risk_category: str
    threshold: float
    model_version: str
    warnings: list[str]
    explanation: Explanation | None = None
