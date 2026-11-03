"""Central configuration; all relative paths resolve from the repository root."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def training_config() -> dict:
    config = json.loads(resolve(os.getenv("FRAUD_CONFIG", "configs/training.json")).read_text())
    if len(config["split_fractions"]) != 5 or abs(sum(config["split_fractions"]) - 1) > 1e-8:
        raise ValueError("Five split fractions must sum to one")
    if any(x <= 0 for x in config["split_fractions"]):
        raise ValueError("Split fractions must be positive")
    for key in ("investigation_cost", "false_positive_cost", "missed_fraud_multiplier"):
        if config[key] < 0:
            raise ValueError(f"{key} must be nonnegative")
    if not 0 < config["review_capacity_fraction"] <= 1:
        raise ValueError("Review capacity must be in (0,1]")
    bands = config["risk_boundaries"]
    if len(bands) != 3 or bands != sorted(set(bands)) or not all(0 < v < 100 for v in bands):
        raise ValueError("Risk boundaries must be three increasing values in (0,100)")
    if config["max_amount"] <= 0 or config["threshold_grid_size"] < 2:
        raise ValueError("Amount limit must be positive and threshold grid needs at least two points")
    return config


def dataset_path() -> Path:
    return resolve(os.getenv("FRAUD_DATASET", "data/raw/financial_fraud_detection_dataset.csv"))


def model_dir() -> Path:
    return resolve(os.getenv("FRAUD_MODEL_DIR", "models"))


def risk_boundaries() -> list[float]:
    default = ",".join(str(v) for v in training_config()["risk_boundaries"])
    values = [float(v) for v in os.getenv("FRAUD_RISK_BOUNDARIES", default).split(",")]
    if len(values) != 3 or values != sorted(set(values)) or not all(0 < v < 100 for v in values):
        raise ValueError("Risk boundaries must be three increasing values in (0,100)")
    return values
