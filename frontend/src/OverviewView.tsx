import { ArrowUpRight, Shield } from "lucide-react";
import { amount, number, percent } from "./client";
import { Analytics, Metrics, ModelInfo, Overview } from "./types";
import { BarPlot, LinePlot, Panel, Risk, Stat } from "./components";
export default function OverviewView({
  overview,
  analytics,
  info,
  metrics,
  onNavigate,
}: {
  overview: Overview;
  analytics: Analytics;
  info: ModelInfo;
  metrics: Metrics;
  onNavigate: (section: string) => void;
}) {
  return (
    <>
      <div className="date-strip">
        <span>
          <i />
          Dataset window
        </span>
        <strong>
          {overview.date_start.slice(0, 10)} — {overview.date_end.slice(0, 10)}
        </strong>
        <span>Currency unspecified · amounts in dataset units</span>
      </div>
      <div className="stats-grid">
        <Stat
          label="Transactions analyzed"
          value={number(overview.total_transactions)}
          detail={`${number(overview.flagged_transactions)} flagged for review`}
        />
        <Stat
          label="Observed fraud rate"
          value={percent(overview.fraud_rate)}
          detail={`${number(overview.fraudulent_transactions)} labeled fraud transactions`}
          tone="risk-stat"
        />
        <Stat
          label="Total transaction value"
          value={number(overview.total_value)}
          detail={`Average ${amount(overview.average_amount)} units`}
        />
        <Stat
          label="Expected fraud exposure"
          value={amount(overview.estimated_exposure)}
          detail="Amount × calibrated probability"
          tone="risk-stat"
        />
      </div>
      <div className="grid two">
        <Panel
          title="Fraud activity"
          sub="Observed fraud rate over time · selected cohort"
        >
          <LinePlot data={analytics.monthly} />
        </Panel>
        <Panel
          title="Risk concentration"
          sub="Observed fraud rate by merchant category"
        >
          <BarPlot data={analytics.by_type} />
        </Panel>
      </div>
      <div className="grid overview-bottom">
        <Panel
          title="Recent labeled fraud"
          sub="Latest known fraud in this offline cohort"
          action={
            <button
              className="text-button"
              onClick={() => onNavigate("transactions")}
            >
              Open queue <ArrowUpRight size={14} />
            </button>
          }
        >
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Transaction</th>
                  <th>Merchant</th>
                  <th>Amount</th>
                  <th>Model risk</th>
                </tr>
              </thead>
              <tbody>
                {overview.recent_fraud.map((t) => (
                  <tr key={t.Transaction_ID}>
                    <td>
                      <strong>{t.Transaction_ID}</strong>
                      <small>{t.Transaction_Date.slice(0, 10)}</small>
                    </td>
                    <td>{t.Merchant_Category}</td>
                    <td className="numeric">{amount(t.Transaction_Amount)}</td>
                    <td>
                      <Risk category={t.risk_category} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
        <Panel title="Model snapshot" sub="Final holdout · frozen policy">
          <div className="model-name">
            <Shield size={21} />
            <div>
              {info.model_name}
              <small>Sigmoid probability calibration</small>
            </div>
          </div>
          <div className="snapshot">
            <span>
              Average precision (PR-AUC)
              <strong>{metrics.test_metrics.pr_auc.toFixed(3)}</strong>
            </span>
            <span>
              Fraud recall
              <strong>{percent(metrics.test_metrics.recall)}</strong>
            </span>
            <span>
              Review threshold
              <strong>{percent(info.threshold)}</strong>
            </span>
            <span>
              Observed fraud value
              <strong>{amount(overview.observed_fraud_value)}</strong>
            </span>
          </div>
          <p className="footnote">
            Offline estimates with documented cost assumptions. No production
            performance claim.
          </p>
          <button
            className="text-button"
            onClick={() => onNavigate("performance")}
          >
            Inspect model evidence <ArrowUpRight size={14} />
          </button>
        </Panel>
      </div>
    </>
  );
}
