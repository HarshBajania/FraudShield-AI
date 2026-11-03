import { ReactNode } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  LineChart,
  Line,
  ReferenceLine,
} from "recharts";
import { amount, percent } from "./client";
import { Prediction } from "./types";

export function Panel({
  title,
  sub,
  children,
  action,
}: {
  title: string;
  sub?: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>{title}</h2>
          {sub && <p>{sub}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}
export function Risk({ category }: { category: string }) {
  return (
    <span className={`badge ${category.toLowerCase()}`}>
      <i />
      {category}
    </span>
  );
}
export function Stat({
  label,
  value,
  detail,
  tone,
}: {
  label: string;
  value: string;
  detail: string;
  tone?: string;
}) {
  return (
    <div className={`stat ${tone || ""}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}
export function BarPlot({
  data,
  dataKey = "fraud_rate",
  percentage = true,
}: {
  data: Record<string, unknown>[];
  dataKey?: string;
  percentage?: boolean;
}) {
  const width = data.some((d) => String(d.name).length > 20) ? 160 : 105;
  return (
    <div
      className="chart"
      role="img"
      aria-label={`${dataKey.replaceAll("_", " ")} chart; hover for values`}
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 8, right: 20, bottom: 10, left: 0 }}
        >
          <CartesianGrid horizontal={false} stroke="#e7e3dd" />
          <YAxis
            dataKey="name"
            type="category"
            width={width}
            tick={{ fontSize: 10 }}
            interval={0}
          />
          <XAxis
            type="number"
            tick={{ fontSize: 10 }}
            tickFormatter={(v) => (percentage ? percent(Number(v)) : String(v))}
          />
          <Tooltip
            formatter={(v) =>
              percentage ? percent(Number(v)) : amount(Number(v))
            }
            contentStyle={{
              borderRadius: 3,
              border: "1px solid #d8d3cc",
              fontSize: 12,
            }}
          />
          <Bar
            dataKey={dataKey}
            fill="#8f3446"
            radius={[0, 2, 2, 0]}
            maxBarSize={25}
            isAnimationActive={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
export function LinePlot({
  data,
  x = "name",
  y = "fraud_rate",
  percentage = true,
  baseline = false,
}: {
  data: Record<string, unknown>[];
  x?: string;
  y?: string;
  percentage?: boolean;
  baseline?: boolean;
}) {
  return (
    <div
      className="chart"
      role="img"
      aria-label={`${y.replaceAll("_", " ")} trend; hover for values`}
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={data}
          margin={{ top: 8, right: 15, bottom: 10, left: 0 }}
        >
          <CartesianGrid vertical={false} stroke="#e7e3dd" />
          <XAxis
            dataKey={x}
            type={x === "x" || x === "threshold" ? "number" : "category"}
            domain={x === "x" ? [0, 1] : undefined}
            tick={{ fontSize: 10 }}
          />
          <YAxis
            tick={{ fontSize: 10 }}
            tickFormatter={(v) => (percentage ? percent(Number(v)) : String(v))}
            domain={percentage ? [0, "auto"] : undefined}
          />
          <Tooltip
            formatter={(v) =>
              percentage ? percent(Number(v)) : amount(Number(v))
            }
          />
          {baseline && (
            <ReferenceLine
              segment={[
                { x: 0, y: 0 },
                { x: 1, y: 1 },
              ]}
              stroke="#b1aba2"
              strokeDasharray="3 3"
            />
          )}
          <Line
            dataKey={y}
            stroke="#8f3446"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
export function PredictionView({ prediction }: { prediction: Prediction }) {
  return (
    <>
      <div className="prediction-summary">
        <div>
          <span className="eyebrow">Calibrated fraud probability</span>
          <strong>{percent(prediction.fraud_probability)}</strong>
          <Risk category={prediction.risk_category} />
        </div>
        <div>
          <span className="eyebrow">Review decision</span>
          <h3>
            {prediction.predicted_class
              ? "Flag for investigation"
              : "Below review threshold"}
          </h3>
          <p>
            Score {prediction.risk_score.toFixed(1)} / 100 · Threshold{" "}
            {percent(prediction.threshold)}
          </p>
        </div>
      </div>
      {prediction.warnings.map((w) => (
        <p className="notice" key={w}>
          {w}
        </p>
      ))}
      {prediction.explanation && (
        <>
          <h3 className="section-label">What influenced this score?</h3>
          <p className="muted">
            Real SHAP contributions in {prediction.explanation.output_space}.
            Positive values increase the base model output.
          </p>
          <div className="factors">
            {prediction.explanation.factors.map((f) => (
              <div className="factor" key={f.feature}>
                <span>{f.feature.replaceAll("_", " ")}</span>
                <div className="factor-track">
                  <i
                    className={f.contribution >= 0 ? "positive" : "negative"}
                    style={{
                      width: `${Math.min(100, (Math.abs(f.contribution) / Math.max(...prediction.explanation!.factors.map((x) => Math.abs(x.contribution)), 0.0001)) * 100)}%`,
                    }}
                  />
                </div>
                <code>
                  {f.contribution >= 0 ? "+" : ""}
                  {f.contribution.toFixed(4)}
                </code>
              </div>
            ))}
          </div>
          <p className="footnote">
            Base {prediction.explanation.base_value.toFixed(4)} → output{" "}
            {prediction.explanation.explained_output.toFixed(4)}.{" "}
            {prediction.explanation.note}
          </p>
        </>
      )}
    </>
  );
}
