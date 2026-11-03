import { useEffect, useState } from "react";
import {
  Shield,
  LayoutDashboard,
  ChartNoAxesCombined,
  ScanSearch,
  FlaskConical,
  Activity,
  Settings,
  RefreshCw,
} from "lucide-react";
import { api } from "./client";
import { Analytics, Metrics, ModelInfo, Overview } from "./types";
import OverviewView from "./OverviewView";
import FraudAnalytics from "./FraudAnalytics";
import Investigation from "./Investigation";
import Predict from "./Predict";
import Performance from "./Performance";
import Monitoring from "./Monitoring";
import useScrollReveal from "./useScrollReveal";

const sections = [
  { id: "overview", name: "Overview", icon: LayoutDashboard },
  { id: "analytics", name: "Analytics", icon: ChartNoAxesCombined },
  { id: "transactions", name: "Transactions", icon: ScanSearch },
  { id: "predict", name: "Score transaction", icon: FlaskConical },
  { id: "performance", name: "Model performance", icon: Activity },
  { id: "monitoring", name: "Data quality", icon: Shield },
];
export default function App() {
  const [section, setSection] = useState("overview"),
    [cohort, setCohort] = useState("test"),
    [reload, setReload] = useState(0);
  const [data, setData] = useState<{
      overview: Overview;
      analytics: Analytics;
      info: ModelInfo;
      metrics: Metrics;
    } | null>(null),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true),
    [connection, setConnection] = useState(false);
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [section]);
  useEffect(() => {
    const close = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setConnection(false);
      }
    };
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    Promise.all([
      api<Overview>(
        `/analytics/overview?cohort=${cohort}`,
        undefined,
        controller.signal,
      ),
      api<Analytics>(
        `/analytics/fraud?cohort=${cohort}`,
        undefined,
        controller.signal,
      ),
      api<ModelInfo>("/model/info", undefined, controller.signal),
      api<Metrics>("/model/metrics", undefined, controller.signal),
    ])
      .then(([overview, analytics, info, metrics]) =>
        setData({ overview, analytics, info, metrics }),
      )
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [cohort, reload]);
  const chosen = sections.find((s) => s.id === section)!;
  const contentRef = useScrollReveal(section, !loading && !error && !!data);
  return (
    <div className="app">
      <header className="horizontal-header">
        <div className="masthead">
          <a
            href="#"
            className="horizontal-brand"
            aria-label="FraudShield home"
            onClick={() => setSection("overview")}
          >
            <svg viewBox="0 0 32 32" width="28" height="28" aria-hidden="true">
              <path d="M7 26V6h19v5H12v5h11v5H12v5Z" fill="currentColor" />
              <path d="M22 24h5v5h-5z" fill="#bc7a65" />
            </svg>
            <span>
              fraudshield<span className="wordmark-dot">.</span>
            </span>
          </a>
          <div className="header-actions">
            <button
              className="icon-button"
              aria-label="Refresh data"
              onClick={() => setReload((x) => x + 1)}
            >
              <RefreshCw size={16} />
            </button>
            <button
              className="icon-button"
              aria-label="Connection settings"
              title="Connection settings"
              aria-expanded={connection}
              onClick={() => setConnection(!connection)}
            >
              <Settings size={16} />
            </button>
          </div>
          {connection && (
            <form
              className="connection-popover"
              onSubmit={(e) => {
                e.preventDefault();
                const key = new FormData(e.currentTarget).get("key") as string;
                key
                  ? sessionStorage.setItem("fraud-api-key", key)
                  : sessionStorage.removeItem("fraud-api-key");
                setConnection(false);
                setReload((x) => x + 1);
              }}
            >
              <label>
                Optional API key
                <input
                  name="key"
                  type="password"
                  autoComplete="off"
                  placeholder="Session only"
                />
              </label>
              <button className="primary">Connect</button>
            </form>
          )}
        </div>
        <nav className="horizontal-nav" aria-label="Platform sections">
          {sections.map((s) => (
            <button
              key={s.id}
              aria-label={s.name}
              aria-current={section === s.id ? "page" : undefined}
              className={section === s.id ? "active" : ""}
              onClick={() => setSection(s.id)}
            >
              <s.icon size={16} />
              <span>{s.name}</span>
            </button>
          ))}
        </nav>
      </header>
      <main>
        <div className="content tab-content" key={section} ref={contentRef}>
          <div className="page-heading">
            <div>
              <h1>{chosen.name}</h1>
              <p>
                {section === "overview"
                  ? "Transaction activity and the current review queue."
                  : section === "analytics"
                    ? "Fraud patterns by date, merchant and location."
                    : section === "transactions"
                      ? "Find a transaction, inspect its score and review the contributing factors."
                      : section === "predict"
                        ? "Enter transaction details to calculate a risk score."
                        : section === "performance"
                          ? "Results from the held-out test window."
                          : "Validate the source data and inspect distribution changes."}
              </p>
            </div>
            {!["predict", "performance", "monitoring"].includes(section) && (
              <label className="cohort-label">
                Analysis cohort
                <select
                  value={cohort}
                  onChange={(e) => setCohort(e.target.value)}
                >
                  <option value="test">Held-out test</option>
                  <option value="all">All transactions</option>
                  <option value="development">Development data</option>
                </select>
              </label>
            )}
          </div>
          {loading ? (
            <div className="loading" role="status">
              <span />
              Loading model evidence and transactions…
            </div>
          ) : error ? (
            <div className="error" role="alert">
              <h2>Connection needs attention</h2>
              <p>{error}</p>
              <p>
                Start the trained backend on port 8000, or set your API key in
                connection settings.
              </p>
              <button
                className="primary"
                onClick={() => setReload((x) => x + 1)}
              >
                Retry connection
              </button>
            </div>
          ) : (
            data && (
              <>
                {cohort !== "test" &&
                  ["overview", "analytics", "transactions"].includes(
                    section,
                  ) && (
                    <p className="notice">
                      This cohort includes development records seen during
                      fitting or selection. Use held-out test data to assess
                      generalization.
                    </p>
                  )}
                {section === "overview" && (
                  <OverviewView
                    overview={data.overview}
                    analytics={data.analytics}
                    info={data.info}
                    metrics={data.metrics}
                    onNavigate={setSection}
                  />
                )}
                {section === "analytics" && (
                  <FraudAnalytics analytics={data.analytics} info={data.info} />
                )}
                {section === "transactions" && (
                  <Investigation cohort={cohort} info={data.info} />
                )}{" "}
                {section === "predict" && <Predict info={data.info} />}{" "}
                {section === "performance" && (
                  <Performance metrics={data.metrics} info={data.info} />
                )}{" "}
                {section === "monitoring" && <Monitoring info={data.info} />}
                <footer>
                  Financial transactions{" "}
                  <span>
                    Model v{data.info.model_version} · Offline analysis
                  </span>
                </footer>
              </>
            )
          )}
        </div>
      </main>
    </div>
  );
}
