import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Search, X, ChevronLeft, ChevronRight } from "lucide-react";
import { api, amount } from "./client";
import { ModelInfo, Prediction, Transaction } from "./types";
import { Panel, PredictionView, Risk } from "./components";

export default function Investigation({
  cohort,
  info,
}: {
  cohort: string;
  info: ModelInfo;
}) {
  const origin = useRef<HTMLButtonElement | null>(null);
  const dialog = useRef<HTMLElement | null>(null);
  const [search, setSearch] = useState(""),
    [location, setLocation] = useState(""),
    [risk, setRisk] = useState(""),
    [merchant, setMerchant] = useState(""),
    [flagged, setFlagged] = useState(""),
    [sort, setSort] = useState("risk_score"),
    [descending, setDescending] = useState(true),
    [page, setPage] = useState(1),
    [min, setMin] = useState(""),
    [max, setMax] = useState("");
  const [list, setList] = useState<{
      items: Transaction[];
      total: number;
    } | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [selected, setSelected] = useState<string | null>(null),
    [detail, setDetail] = useState<{
      transaction: Transaction;
      prediction: Prediction;
    } | null>(null),
    [detailError, setDetailError] = useState("");
  useEffect(() => {
    setPage(1);
  }, [
    search,
    location,
    risk,
    merchant,
    flagged,
    sort,
    min,
    max,
    cohort,
    descending,
  ]);
  useEffect(() => {
    const c = new AbortController();
    setBusy(true);
    setError("");
    const timer = setTimeout(() => {
      const q = new URLSearchParams({
        cohort,
        page: String(page),
        page_size: "15",
        search,
        sort,
        descending: String(descending),
      });
      if (location) q.set("location", location);
      if (risk) q.set("risk", risk);
      if (merchant) q.set("merchant", merchant);
      if (flagged) q.set("flagged", flagged);
      if (min) q.set("min_amount", min);
      if (max) q.set("max_amount", max);
      api<{ items: Transaction[]; total: number }>(
        `/transactions?${q}`,
        undefined,
        c.signal,
      )
        .then(setList)
        .catch((e) => {
          if (e.name !== "AbortError") setError(e.message);
        })
        .finally(() => {
          if (!c.signal.aborted) setBusy(false);
        });
    }, 200);
    return () => {
      clearTimeout(timer);
      c.abort();
    };
  }, [
    cohort,
    page,
    search,
    location,
    risk,
    merchant,
    flagged,
    sort,
    min,
    max,
    descending,
  ]);
  useEffect(() => {
    if (!selected) return;
    const c = new AbortController();
    setDetail(null);
    setDetailError("");
    api<{ transaction: Transaction; prediction: Prediction }>(
      `/transactions/${encodeURIComponent(selected)}`,
      undefined,
      c.signal,
    )
      .then(setDetail)
      .catch((e) => {
        if (e.name !== "AbortError") setDetailError(e.message);
      });
    return () => c.abort();
  }, [selected]);
  useEffect(() => {
    if (!selected) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setSelected(null);
      if (e.key === "Tab") {
        const controls = dialog.current?.querySelectorAll<HTMLElement>(
          "button, input, select, textarea, a[href]",
        );
        if (!controls?.length) return;
        const first = controls[0],
          last = controls[controls.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    window.addEventListener("keydown", handler);
    const scroll = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", handler);
      document.body.style.overflow = scroll;
      origin.current?.focus();
    };
  }, [selected]);
  return (
    <>
      <Panel
        title="Transaction ledger"
        sub="Labels and model decisions are separate fields. Select an ID to investigate."
      >
        <div className="filters">
          <label className="search">
            <Search size={16} />
            <input
              aria-label="Search transaction ID"
              placeholder="Search transaction ID"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </label>
          <select
            aria-label="Location filter"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          >
            <option value="">All locations</option>
            {info.categories.Location.map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
          <select
            aria-label="Merchant filter"
            value={merchant}
            onChange={(e) => setMerchant(e.target.value)}
          >
            <option value="">All merchants</option>
            {info.categories.Merchant_Category.map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
          <select
            aria-label="Risk filter"
            value={risk}
            onChange={(e) => setRisk(e.target.value)}
          >
            <option value="">All risk bands</option>
            {["Low", "Moderate", "High", "Critical"].map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
          <select
            aria-label="Decision filter"
            value={flagged}
            onChange={(e) => setFlagged(e.target.value)}
          >
            <option value="">All decisions</option>
            <option value="true">Flagged</option>
            <option value="false">Below threshold</option>
          </select>
          <input
            type="number"
            min="0"
            max={info.training_config.max_amount}
            aria-label="Minimum amount"
            placeholder="Min amount"
            value={min}
            onChange={(e) => setMin(e.target.value)}
          />
          <input
            type="number"
            min="0"
            max={info.training_config.max_amount}
            aria-label="Maximum amount"
            placeholder="Max amount"
            value={max}
            onChange={(e) => setMax(e.target.value)}
          />
          <select
            aria-label="Sort transactions"
            value={sort}
            onChange={(e) => setSort(e.target.value)}
          >
            <option value="risk_score">Sort: risk score</option>
            <option value="Transaction_Amount">Sort: amount</option>
            <option value="Transaction_Date">Sort: date</option>
          </select>
          <button
            className="secondary"
            onClick={() => setDescending((v) => !v)}
          >
            {descending ? "Descending" : "Ascending"}
          </button>
        </div>
        {error ? (
          <p className="error" role="alert">
            {error}
          </p>
        ) : (
          <>
            <div className="table-scroll" aria-busy={busy}>
              <table>
                <thead>
                  <tr>
                    <th>Transaction / date</th>
                    <th>Merchant / channel</th>
                    <th>Location</th>
                    <th>Amount</th>
                    <th>Risk score</th>
                    <th>Decision</th>
                    <th>Known label</th>
                  </tr>
                </thead>
                <tbody>
                  {list?.items.map((t) => (
                    <tr key={t.Transaction_ID}>
                      <td>
                        <button
                          className="transaction-link"
                          onClick={(event) => {
                            origin.current = event.currentTarget;
                            setSelected(t.Transaction_ID);
                          }}
                        >
                          {t.Transaction_ID}
                        </button>
                        <small>
                          {t.Transaction_Date.replace("T", " ").slice(0, 16)}
                        </small>
                      </td>
                      <td>
                        {t.Merchant_Category}
                        <small>{t.Payment_Method}</small>
                      </td>
                      <td>{t.Location}</td>
                      <td className="numeric">
                        {amount(t.Transaction_Amount)}
                      </td>
                      <td>
                        <div className="risk-inline">
                          <strong>{t.risk_score.toFixed(1)}</strong>
                          <Risk category={t.risk_category} />
                        </div>
                      </td>
                      <td>
                        <span
                          className={
                            t.predicted_class ? "decision flagged" : "decision"
                          }
                        >
                          {t.predicted_class ? "Review" : "Below threshold"}
                        </span>
                      </td>
                      <td>{t.Fraudulent ? "Fraud" : "Legitimate"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!busy && list?.items.length === 0 && (
                <div className="empty">
                  No transactions match these filters.
                </div>
              )}
              {busy && (
                <div className="table-loading" role="status">
                  Updating ledger…
                </div>
              )}
            </div>
            <div className="pagination">
              <span>
                {list?.total ?? 0} transactions · Page {page} of{" "}
                {Math.max(1, Math.ceil((list?.total ?? 0) / 15))}
              </span>
              <div>
                <button
                  className="icon-button"
                  aria-label="Previous page"
                  disabled={page === 1 || busy}
                  onClick={() => setPage((p) => p - 1)}
                >
                  <ChevronLeft size={17} />
                </button>
                <button
                  className="icon-button"
                  aria-label="Next page"
                  disabled={busy || page * 15 >= (list?.total ?? 0)}
                  onClick={() => setPage((p) => p + 1)}
                >
                  <ChevronRight size={17} />
                </button>
              </div>
            </div>
          </>
        )}
      </Panel>
      {selected &&
        createPortal(
          <div className="drawer-overlay" onClick={() => setSelected(null)}>
            <section
              ref={dialog}
              role="dialog"
              aria-modal="true"
              aria-labelledby="detail-title"
              className="drawer"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="drawer-heading">
                <div>
                  <span className="eyebrow">TRANSACTION INVESTIGATION</span>
                  <h2 id="detail-title">{selected}</h2>
                </div>
                <button
                  className="icon-button"
                  autoFocus
                  aria-label="Close transaction details"
                  onClick={() => setSelected(null)}
                >
                  <X size={20} />
                </button>
              </div>
              {detailError ? (
                <p role="alert" className="error">
                  {detailError}
                </p>
              ) : detail ? (
                <>
                  <div className="detail-grid">
                    <span>
                      Amount
                      <strong>
                        {amount(detail.transaction.Transaction_Amount)} units
                      </strong>
                    </span>
                    <span>
                      Merchant
                      <strong>{detail.transaction.Merchant_Category}</strong>
                    </span>
                    <span>
                      Location<strong>{detail.transaction.Location}</strong>
                    </span>
                    <span>
                      Known outcome
                      <strong>
                        {detail.transaction.Fraudulent ? "Fraud" : "Legitimate"}
                      </strong>
                    </span>
                    <span>
                      Timestamp
                      <strong>
                        {detail.transaction.Transaction_Date.replace("T", " ")}
                      </strong>
                    </span>
                    <span>
                      Cohort
                      <strong>{detail.transaction.evaluation_cohort}</strong>
                    </span>
                  </div>
                  <PredictionView
                    prediction={{
                      ...detail.prediction,
                      warnings: detail.prediction.warnings.filter(
                        (warning) =>
                          warning !==
                          "Missing optional values were imputed using the fitted training pipeline.",
                      ),
                    }}
                  />
                </>
              ) : (
                <div className="loading" role="status">
                  Calculating SHAP explanation…
                </div>
              )}
            </section>
          </div>,
          document.body,
        )}
    </>
  );
}
