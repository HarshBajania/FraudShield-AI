import { Analytics, ModelInfo } from "./types";
import { BarPlot, LinePlot, Panel } from "./components";
export default function FraudAnalytics({
  analytics,
  info,
}: {
  analytics: Analytics;
  info: ModelInfo;
}) {
  return (
    <div className="grid two">
      <Panel
        title="Fraud rate over time"
        sub="Observed labels; edge months may be partial"
      >
        <LinePlot data={analytics.monthly} />
      </Panel>
      <Panel
        title="Fraud by location"
        sub="Fraud rate, rather than volume alone"
      >
        <BarPlot data={analytics.by_location} />
      </Panel>
      <Panel
        title="Merchant categories"
        sub="Observed fraud rate by transaction category"
      >
        <BarPlot data={analytics.by_type} />
      </Panel>
      <Panel title="Amount bands" sub="Fraud rate by transaction value">
        <BarPlot data={analytics.by_amount} />
      </Panel>
      <Panel
        title="Probability distribution"
        sub="Calibrated model probabilities; counts per band"
      >
        <BarPlot
          data={analytics.probability_distribution}
          dataKey="count"
          percentage={false}
        />
      </Panel>
      <Panel
        title="Flagged transaction trend"
        sub="Review-policy decisions per month"
      >
        <LinePlot data={analytics.monthly} y="flagged" percentage={false} />
      </Panel>
      <Panel
        title="Fraud value trend"
        sub="Sum of observed fraudulent transaction amounts"
      >
        <LinePlot data={analytics.monthly} y="fraud_value" percentage={false} />
      </Panel>
      <Panel
        title="High-risk score trend"
        sub={`Transactions with score ≥ ${info.risk_boundaries[1]}; distinct from review decisions`}
      >
        <LinePlot data={analytics.monthly} y="high_risk" percentage={false} />
      </Panel>
      <Panel
        title="Payment methods"
        sub="Observed fraud rate by payment channel"
      >
        <BarPlot data={analytics.by_payment} />
      </Panel>
    </div>
  );
}
