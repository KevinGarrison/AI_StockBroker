import { useState } from "react";
import SecFileModal from "./SecFileModal";

// Helper: gibt Farben nach Recommendation zurück
function badgeColor(rec) {
  if (rec.toUpperCase().includes("BUY")) return "success";
  if (rec.toUpperCase().includes("SELL")) return "danger";
  if (rec.toUpperCase().includes("HOLD")) return "warning text-dark";
  return "secondary";
}

function RecommendationBox({ analysis }) {
  const [showModal, setShowModal] = useState(false);
  
  if (!analysis) return null;

  const {
    technical,
    fundamental,
    sentiment,
    recommendation,
    justification,
    meta,
  } = analysis;

  return (
    <div className="bg-white rounded shadow p-4 hover-box mb-4">
      {/* Header */}
      <div className="d-flex align-items-center mb-3" style={{ gap: 10 }}>
        <span style={{ fontSize: 24, color: "#FFD600" }}>🤖</span>
        <h4 className="fw-bold text-primary mb-0">
          AI Analysis Recommendation
        </h4>
      </div>
      <div className="row g-3">
        {/* Technical */}
        <div className="col-md-4">
          <div className="p-3 rounded bg-light border h-100">
            <div className="fw-bold mb-2" style={{ color: "#1e88e5" }}>
              <span role="img" aria-label="tech" style={{ marginRight: 6 }}>
                📈
              </span>
              Technical
            </div>
            <ul className="mb-0 small">
              {technical && technical.map((item, i) => <li key={i}>{item}</li>)}
            </ul>
          </div>
        </div>
        {/* Fundamental */}
        <div className="col-md-4">
          <div className="p-3 rounded bg-light border h-100">
            <div className="fw-bold mb-2" style={{ color: "#43a047" }}>
              <span
                role="img"
                aria-label="fundamental"
                style={{ marginRight: 6 }}
              >
                💹
              </span>
              Fundamental
            </div>
            <ul className="mb-0 small">
              {fundamental &&
                fundamental.map((item, i) => <li key={i}>{item}</li>)}
            </ul>
          </div>
        </div>
        {/* Sentiment */}
        <div className="col-md-4">
          <div className="p-3 rounded bg-light border h-100">
            <div className="fw-bold mb-2" style={{ color: "#ff9800" }}>
              <span
                role="img"
                aria-label="sentiment"
                style={{ marginRight: 6 }}
              >
                💬
              </span>
              Sentiment
            </div>
            <ul className="mb-0 small">
              {sentiment && sentiment.map((item, i) => <li key={i}>{item}</li>)}
            </ul>
          </div>
        </div>
      </div>
      {/* Recommendation */}
      {recommendation && (
        <div className="d-flex align-items-center mt-4 mb-1">
          <span
            className={`badge rounded-pill px-3 py-2 me-3 bg-${badgeColor(
              recommendation
            )}`}
            style={{ fontSize: 18, letterSpacing: 1 }}
          >
            {recommendation}
          </span>
          <span className="fw-bold text-secondary" style={{ fontSize: 15 }}>
            {justification}
          </span>
        </div>
      )}
      {/* Meta */}
      <div className="mt-4 p-3 small bg-light border rounded position-relative">
        <div className="fw-bold mb-1 text-primary d-flex justify-content-between align-items-center">
          Meta Data SEC Files
          <button
            className="btn btn-sm btn-outline-primary"
            style={{ fontSize: 13 }}
            onClick={() => setShowModal(true)}
          >
            Open Meta Data
          </button>
        </div>
        <div>
          {meta.form && (
            <>
              <b>Form:</b> {meta.form} <br />
            </>
          )}
          {meta.reportDate && (
            <>
              <b>Report Date:</b> {meta.reportDate} <br />
            </>
          )}
          {meta.accessionNumber && (
            <>
              <b>Accession Number:</b> {meta.accessionNumber} <br />
            </>
          )}
          {meta.cik && (
            <>
              <b>CIK:</b> {meta.cik}
            </>
          )}
          {!meta.form &&
            !meta.reportDate &&
            !meta.accessionNumber &&
            !meta.cik && (
              <span className="text-muted">No meta data found.</span>
            )}
        </div>
        {/* Das Modal */}
        <SecFileModal
          meta={meta}
          show={showModal}
          onClose={() => setShowModal(false)}
        />
      </div>
    </div>
  );
}

export default RecommendationBox;
