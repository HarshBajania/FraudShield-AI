import { useEffect, useState } from "react";
import { api, number, percent } from "./client";
import { ModelInfo } from "./types";
import { Panel, Stat } from "./components";
type MonitoringData = {
  data_quality: {
    rows: number;
    fraud_rate: number;
    zero_amounts: number;
    amount_outliers_iqr: number;
    missing: Record<string, number>;
    excluded_features: string[];
    availability_warning: string;
  };
  train_test_drift: {
    numeric: Record<
      string,
      { ks_statistic: number; p_value: number; warning: boolean }
    >;
    categorical: Record<string, { total_variation: number; warning: boolean }>;
    note: string;
  };
  note: string;
};
export default function Monitoring({ info }: { info: ModelInfo }) {
  const [data, setData] = useState<MonitoringData | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    const c = new AbortController();
    api<MonitoringData>("/monitoring", undefined, c.signal)
      .then(setData)
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => c.abort();
  }, []);
  if (error)
    return (
      <p role="alert" className="error">
        {error}
      </p>
    );
  if (!data)
    return (
      <div role="status" className="loading">
        Loading data-quality diagnostics…
      </div>
    );
  return (
    <>
      <div className="stats-grid">
        <Stat
          label="Validated source rows"
          value={number(data.data_quality.rows)}
          detail="Unique transaction identifiers"
        />
        <Stat
          label="Source fraud rate"
          value={percent(data.data_quality.fraud_rate)}
          detail="Full financial dataset"
        />
        <Stat
          label="Missing source values"
          value={number(
            Object.values(data.data_quality.missing).reduce((a, b) => a + b, 0),
          )}
          detail="Required inputs validated before training"
        />
        <Stat
          label="Amount outliers"
          value={number(data.data_quality.amount_outliers_iqr)}
          detail={`${data.data_quality.zero_amounts} zero amounts · IQR diagnostics`}
        />
      </div>
      <div className="grid two">
        <Panel
          title="Numerical drift"
          sub="Fit window vs test window · KS distribution comparison"
        >
          <table>
            <thead>
              <tr>
                <th>Feature</th>
                <th>KS statistic</th>
                <th>P-value</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.train_test_drift.numeric).map(([key, v]) => (
                <tr key={key}>
                  <td>{key.replaceAll("_", " ")}</td>
                  <td>{v.ks_statistic.toFixed(3)}</td>
                  <td>{v.p_value.toFixed(4)}</td>
                  <td>
                    <span className={v.warning ? "badge high" : "badge low"}>
                      {v.warning ? "Investigate" : "Within reference"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
        <Panel
          title="Categorical drift"
          sub="Total variation distance against training distribution"
        >
          <table>
            <thead>
              <tr>
                <th>Feature</th>
                <th>Distance</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.train_test_drift.categorical).map(
                ([key, v]) => (
                  <tr key={key}>
                    <td>{key.replaceAll("_", " ")}</td>
                    <td>{v.total_variation.toFixed(3)}</td>
                    <td>
                      <span className={v.warning ? "badge high" : "badge low"}>
                        {v.warning ? "Investigate" : "Within reference"}
                      </span>
                    </td>
                  </tr>
                ),
              )}
            </tbody>
          </table>
        </Panel>
      </div>
      <p className="notice">
        {data.train_test_drift.note} {data.note}
      </p>
      <Panel
        title="Chronological experiment lineage"
        sub="Five independent windows; no test-driven tuning"
      >
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Window</th>
                <th>Records</th>
                <th>Fraud</th>
                <th>Start</th>
                <th>End</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(info.split_windows).map(([key, v]) => (
                <tr key={key}>
                  <td>{key}</td>
                  <td>{v.rows}</td>
                  <td>{v.fraud}</td>
                  <td>{v.start}</td>
                  <td>{v.end}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="footnote">
          Dataset SHA-256: <code>{info.dataset_version}</code>
        </p>
      </Panel>
      <Panel
        title="Data availability & limitations"
        sub="Boundaries of the evidence"
      >
        <p className="notice">{data.data_quality.availability_warning}</p>
        <ul className="limitations">
          {info.limitations.map((v) => (
            <li key={v}>{v}</li>
          ))}
        </ul>
      </Panel>
    </>
  );
}
