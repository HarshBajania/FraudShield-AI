import { Metrics, ModelInfo } from "./types";
import { amount, number, percent } from "./client";
import { BarPlot, LinePlot, Panel, Stat } from "./components";

export default function Performance({
  metrics,
  info,
}: {
  metrics: Metrics;
  info: ModelInfo;
}) {
  const m = metrics.test_metrics,
    b = metrics.constant_baseline_test,
    matrix = m.confusion_matrix;
  return (
    <>
      <div className="date-strip">
        <span>FINAL CHRONOLOGICAL HOLDOUT</span>
        <strong>
          {number(m.rows)} transactions · {percent(m.prevalence)} fraud
          prevalence
        </strong>
        <span>
          Calibration and threshold selection completed before testing
        </span>
      </div>
      <div className="stats-grid">
        <Stat
          label="Precision"
          value={percent(m.precision)}
          detail="Fraud among flagged transactions"
        />
        <Stat
          label="Recall / fraud capture"
          value={percent(m.recall)}
          detail="Fraud transactions flagged"
        />
        <Stat
          label="Average precision (PR-AUC)"
          value={m.pr_auc.toFixed(3)}
          detail={`Constant baseline ${b.pr_auc.toFixed(3)}`}
        />
        <Stat
          label="ROC-AUC"
          value={m.roc_auc.toFixed(3)}
          detail={`F1 ${m.f1.toFixed(3)} · Brier ${m.brier_score.toFixed(4)}`}
        />
      </div>
      <p className="notice">
        Test PR-AUC 95% bootstrap interval:{" "}
        {metrics.test_uncertainty.pr_auc_95_percentile_interval
          .map((v) => v.toFixed(3))
          .join("–")}
        . Fixed-model resampling measures holdout uncertainty, not deployment
        reliability.
      </p>
      <div className="grid two">
        <Panel
          title="Precision–recall curve"
          sub="X: recall · Y: precision · held-out test"
        >
          <LinePlot data={metrics.curves.pr} x="x" y="y" />
        </Panel>
        <Panel
          title="ROC curve"
          sub="X: false positive rate · Y: true positive rate"
        >
          <LinePlot data={metrics.curves.roc} x="x" y="y" baseline />
        </Panel>
        <Panel
          title="Confusion matrix"
          sub="Rows: actual label · columns: predicted label"
        >
          <div className="confusion">
            <span />
            <span>Legitimate</span>
            <span>Fraud</span>
            <span>Actual legitimate</span>
            <div className="tn">
              <strong>{matrix[0][0]}</strong>
              <small>True negatives</small>
            </div>
            <div className="fp">
              <strong>{matrix[0][1]}</strong>
              <small>False positives</small>
            </div>
            <span>Actual fraud</span>
            <div className="fn">
              <strong>{matrix[1][0]}</strong>
              <small>False negatives</small>
            </div>
            <div className="tp">
              <strong>{matrix[1][1]}</strong>
              <small>True positives</small>
            </div>
          </div>
          <div className="metric-row">
            <span>
              False positive rate{" "}
              <strong>{percent(m.false_positive_rate)}</strong>
            </span>
            <span>
              False negative rate{" "}
              <strong>{percent(m.false_negative_rate)}</strong>
            </span>
          </div>
        </Panel>
        <Panel
          title="Business scenario"
          sub="Dataset units; illustrative configured costs"
        >
          <div className="snapshot">
            <span>
              Fraud amount captured
              <strong>{amount(m.fraud_amount_captured)}</strong>
            </span>
            <span>
              Fraud amount missed
              <strong>{amount(m.fraud_amount_missed)}</strong>
            </span>
            <span>
              Legitimate value flagged
              <strong>{amount(m.legitimate_amount_flagged)}</strong>
            </span>
            <span>
              Investigation cost<strong>{amount(m.investigation_cost)}</strong>
            </span>
            <span>
              Estimated total cost<strong>{amount(m.estimated_cost)}</strong>
            </span>
            <span>
              No-signal baseline cost<strong>{amount(b.estimated_cost)}</strong>
            </span>
            <span>
              Amount capture rate
              <strong>{percent(m.amount_capture_rate)}</strong>
            </span>
            <span>
              Review rate<strong>{percent(m.review_rate)}</strong>
            </span>
          </div>
          <p className="footnote">
            Review cost {info.training_config.investigation_cost} per flag;
            false-positive friction {info.training_config.false_positive_cost};
            missed loss {info.training_config.missed_fraud_multiplier} × amount.
            Costs are assumptions, not measured outcomes.
          </p>
        </Panel>
        <Panel
          title="Threshold economics"
          sub="Policy window only · X: threshold · Y: estimated cost"
        >
          <LinePlot
            data={metrics.threshold_analysis}
            x="threshold"
            y="estimated_cost"
            percentage={false}
          />
          <p className="footnote">
            Frozen threshold {percent(info.trained_threshold)} minimizes
            policy-window cost with review rate ≤{" "}
            {percent(info.training_config.review_capacity_fraction)}. Serving
            threshold: {percent(info.threshold)}. Test metrics remain frozen.
          </p>
        </Panel>
        <Panel
          title="Global model explanations"
          sub="Mean absolute SHAP on up to 200 held-out records; base estimator"
        >
          <BarPlot
            data={metrics.global_explanations.slice(0, 7).map((x) => ({
              name: x.feature.replaceAll("_", " "),
              importance: x.mean_absolute_shap,
            }))}
            dataKey="importance"
            percentage={false}
          />
        </Panel>
      </div>
      <Panel
        title="Model comparison"
        sub="Tuning PR-AUC and calibrated policy-window outcomes; final test used only for selected model"
      >
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Candidate</th>
                <th>Tuning PR-AUC</th>
                <th>Policy PR-AUC</th>
                <th>Policy precision</th>
                <th>Policy recall</th>
                <th>Policy cost</th>
                <th>Threshold</th>
              </tr>
            </thead>
            <tbody>
              {metrics.model_comparison.map((row) => (
                <tr
                  className={
                    row.model === info.model_name ? "selected-row" : ""
                  }
                  key={row.model}
                >
                  <td>
                    <strong>{row.model}</strong>
                    {row.model === info.model_name && (
                      <small>Selected on policy-window cost</small>
                    )}
                  </td>
                  <td>{row.tuning_pr_auc.toFixed(3)}</td>
                  <td>{row.policy_metrics.pr_auc.toFixed(3)}</td>
                  <td>{percent(row.policy_metrics.precision)}</td>
                  <td>{percent(row.policy_metrics.recall)}</td>
                  <td>{amount(row.policy_metrics.estimated_cost)}</td>
                  <td>{percent(row.policy_metrics.threshold)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="footnote">
          Precision@{m.k}: {percent(m.precision_at_k)} · Recall@{m.k}:{" "}
          {percent(m.recall_at_k)}. Ranking budget ={" "}
          {percent(info.training_config.review_capacity_fraction)} of test
          transactions. {info.selection_reason}
        </p>
      </Panel>
    </>
  );
}
