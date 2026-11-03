import { FormEvent, useState } from "react";
import { api, percent } from "./client";
import { ModelInfo, Prediction } from "./types";
import { Panel, PredictionView } from "./components";

export default function Predict({ info }: { info: ModelInfo }) {
  const [prediction, setPrediction] = useState<Prediction | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [batch, setBatch] = useState(""),
    [batchResults, setBatchResults] = useState<Prediction[] | null>(null),
    [batchBusy, setBatchBusy] = useState(false),
    [batchError, setBatchError] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setPrediction(null);
    setBusy(true);
    const f = new FormData(event.currentTarget);
    const body: Record<string, unknown> = {
      Transaction_Date: f.get("Transaction_Date"),
      Transaction_Amount: Number(f.get("Transaction_Amount")),
      Is_International: Number(f.get("Is_International")),
      Account_Age_Days:
        f.get("Account_Age_Days") === ""
          ? null
          : Number(f.get("Account_Age_Days")),
    };
    Object.keys(info.categories).forEach((k) => (body[k] = f.get(k) || null));
    try {
      setPrediction(
        await api<Prediction>("/predict", {
          method: "POST",
          body: JSON.stringify(body),
        }),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function scoreBatch() {
    setBatchError("");
    setBatchResults(null);
    setBatchBusy(true);
    try {
      const parsed: unknown = JSON.parse(batch);
      if (!Array.isArray(parsed) || !parsed.length || parsed.length > 500)
        throw new Error("Provide a JSON array of 1–500 transactions.");
      setBatchResults(
        await api<Prediction[]>("/predict/batch", {
          method: "POST",
          body: JSON.stringify({ transactions: parsed }),
        }),
      );
    } catch (e) {
      setBatchError((e as Error).message);
    } finally {
      setBatchBusy(false);
    }
  }
  return (
    <>
      <div className="grid prediction-grid">
        <Panel
          title="Transaction input"
          sub="Required fields are marked *. Optional missing values use training-fitted imputation."
        >
          <form onSubmit={submit} className="prediction-form">
            <label>
              Transaction timestamp *
              <input
                type="datetime-local"
                name="Transaction_Date"
                required
                min="2000-01-01T00:00"
                max="2100-12-31T23:59"
              />
            </label>
            <label>
              Transaction amount *
              <input
                type="number"
                name="Transaction_Amount"
                min="0"
                max={info.training_config.max_amount}
                step="0.01"
                placeholder="Amount in dataset units"
                required
              />
            </label>
            <label>
              International transaction *
              <select name="Is_International">
                <option value="0">No</option>
                <option value="1">Yes</option>
              </select>
            </label>
            <label>
              Account age (days)
              <input
                type="number"
                name="Account_Age_Days"
                min="0"
                max="100000"
                step="1"
                placeholder="Leave empty if unknown"
              />
            </label>
            {Object.entries(info.categories).map(([key, values]) => (
              <label key={key}>
                {key.replaceAll("_", " ")}
                <select name={key}>
                  <option value="">Unknown / missing</option>
                  {values.map((v) => (
                    <option key={v}>{v}</option>
                  ))}
                </select>
              </label>
            ))}
            <p className="footnote full-width">
              Source timezone and currency are undocumented. Use dataset-local
              time. Historical spend, identifiers and suspicious-keyword fields
              are intentionally excluded.
            </p>
            <button className="primary full-width" disabled={busy}>
              {busy ? "Scoring transaction…" : "Calculate fraud risk"}
            </button>
          </form>
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
        </Panel>
        <Panel
          title="Risk assessment"
          sub={`Model v${info.model_version} · Review threshold ${percent(info.threshold)}`}
        >
          {prediction ? (
            <PredictionView prediction={prediction} />
          ) : (
            <div className="prediction-empty">
              <span className="empty-symbol">01</span>
              <h3>Evidence starts with a transaction</h3>
              <p>
                Enter the available transaction details to calculate a
                calibrated probability, review decision and real SHAP
                explanation.
              </p>
            </div>
          )}
          <div className="risk-legend">
            <span className="eyebrow">CONFIGURABLE DISPLAY BANDS</span>
            <p>
              Low &lt; {info.risk_boundaries[0]} · Moderate &lt;{" "}
              {info.risk_boundaries[1]} · High &lt; {info.risk_boundaries[2]} ·
              Critical ≥ {info.risk_boundaries[2]}
            </p>
            <small>
              Score = probability × 100. Display bands are conventions; the
              review decision uses the optimized threshold.
            </small>
          </div>
        </Panel>
      </div>
      <Panel
        title="Batch scoring"
        sub="Paste a JSON array using the /predict schema. Up to 500 transactions; explanations disabled for faster review."
      >
        <label className="batch-label">
          Transactions JSON
          <textarea
            value={batch}
            onChange={(e) => setBatch(e.target.value)}
            rows={5}
            placeholder='[{"Transaction_Date":"2024-02-01T10:00:00","Transaction_Amount":100,"Is_International":0}]'
          />
        </label>
        <button
          className="secondary"
          onClick={scoreBatch}
          disabled={batchBusy || !batch.trim()}
        >
          {batchBusy ? "Scoring batch…" : "Score batch"}
        </button>
        {batchError && (
          <p role="alert" className="error">
            {batchError}
          </p>
        )}
        {batchResults && (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Row</th>
                  <th>Probability</th>
                  <th>Risk score</th>
                  <th>Category</th>
                  <th>Decision</th>
                </tr>
              </thead>
              <tbody>
                {batchResults.map((p, i) => (
                  <tr key={i}>
                    <td>{i + 1}</td>
                    <td>{percent(p.fraud_probability)}</td>
                    <td>{p.risk_score.toFixed(1)}</td>
                    <td>{p.risk_category}</td>
                    <td>{p.predicted_class ? "Review" : "Below threshold"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </>
  );
}
