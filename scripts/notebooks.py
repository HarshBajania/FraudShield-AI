"""Make the preserved notebook portable and create thin reproducible workflow notebooks."""
import json
from pathlib import Path
from src.config import ROOT


def notebook(path, title, cells):
    def markdown(text):
        return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}
    def code(text):
        return {"cell_type": "code", "metadata": {}, "source": text.splitlines(keepends=True), "execution_count": None, "outputs": []}
    setup = "from pathlib import Path\nimport sys, json\nROOT = Path.cwd() if (Path.cwd() / 'src').exists() else Path.cwd().parent\nsys.path.insert(0, str(ROOT))\nimport pandas as pd\nfrom IPython.display import display, Image\n"
    data = {"nbformat": 4, "nbformat_minor": 5, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}}, "cells": [markdown(title), code(setup)] + [code(c) for c in cells]}
    for i, cell in enumerate(data["cells"]):
        cell["id"] = f"workflow-{i:03}"
    path.write_text(json.dumps(data, indent=1), encoding="utf-8")


def run():
    original = ROOT / "notebooks/01_data_understanding.ipynb"
    document = json.loads(original.read_text(encoding="utf-8"))
    for cell in document["cells"]:
        source = "".join(cell.get("source", []))
        if 'pd.read_csv("C:/Users/harsh/projects/FraudShield-AI/data/raw/' in source:
            variable = "df_credit" if "credit_card" in source else "df_financial"
            filename = "credit_card_fraud_dataset.csv" if "credit_card" in source else "financial_fraud_detection_dataset.csv"
            cell["source"] = ["from pathlib import Path\n", "ROOT = Path.cwd() if (Path.cwd() / 'data').exists() else Path.cwd().parent\n", f'{variable} = pd.read_csv(ROOT / "data/raw/{filename}")\n']
    original.write_text(json.dumps(document, indent=1), encoding="utf-8")
    notebook(ROOT / "notebooks/02_eda.ipynb", "# Source audit and exploratory evidence\nRun `python -m scripts.audit` first. Outputs below are generated from the supplied CSVs. Original analysis is retained in 01_data_understanding.ipynb.", [
        "audit = json.loads((ROOT / 'docs/reports/audit.json').read_text())\ndisplay(audit)",
        "display(Image(filename=str(ROOT / 'docs/reports/eda.png')))",
        "from src.data import load_financial\nfrom src.config import dataset_path\nframe, report = load_financial(dataset_path())\ndisplay(frame.groupby('Fraudulent').Transaction_Amount.describe())\ndisplay(frame.groupby('Payment_Method').Fraudulent.agg(['count','mean']))\ndisplay(frame.isna().sum())",
    ])
    notebook(ROOT / "notebooks/03_feature_engineering.ipynb", "# Inference-time features and leakage boundaries\nNo historical or future aggregates are generated. Inspect the same transformer used by training and serving.", [
        "from src.data import FEATURES, EXCLUDED, load_financial\nfrom src.config import dataset_path\nfrom src.features import TransactionFeatures\nframe, _ = load_financial(dataset_path())\ndisplay({'included': FEATURES, 'excluded': EXCLUDED})\ndisplay(TransactionFeatures().transform(frame[FEATURES].head()))",
        "from scripts.train import split_windows\nfrom src.config import training_config\nwindows = split_windows(frame, training_config()['split_fractions'])\ndisplay(pd.DataFrame([{'rows': len(w), 'start': w.Transaction_Date.min(), 'end': w.Transaction_Date.max(), 'fraud': w.Fraudulent.sum()} for w in windows], index=['fit','tune','calibration','policy','test']))",
    ])
    notebook(ROOT / "notebooks/04_model_evaluation.ipynb", "# Actual model evidence\nRun `python -m scripts.train` first. Model selection uses policy data; test is reported only after selection. SHAP explains the base estimator before calibration.", [
        "metadata = json.loads((ROOT / 'models/metadata.json').read_text())\ndisplay(pd.DataFrame(metadata['model_comparison']))\ndisplay(pd.Series(metadata['test_metrics']))\ndisplay(metadata['test_uncertainty'])",
        "import matplotlib.pyplot as plt\nfig, ax = plt.subplots(1,2,figsize=(10,4))\nfor axis, key, label in zip(ax, ['pr','roc'], ['Recall / precision', 'False positive rate / true positive rate']):\n    curve = pd.DataFrame(metadata['curves'][key])\n    axis.plot(curve.x, curve.y, color='#8f3446')\n    axis.set_title(label)\nplt.show()",
        "display(pd.DataFrame(metadata['global_explanations']).head(15))\ndisplay(metadata['limitations'])",
    ])


if __name__ == '__main__':
    run()
