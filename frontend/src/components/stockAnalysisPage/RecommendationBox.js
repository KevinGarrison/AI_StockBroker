import { useState } from "react";
import SecFileModal from "./SecFileModal";

function badgeColor(rec) {
  if (rec.toUpperCase().includes("BUY")) return "success";
  if (rec.toUpperCase().includes("SELL")) return "danger";
  if (rec.toUpperCase().includes("HOLD")) return "warning text-dark";
  return "secondary";
}

function RecommendationBox({ analysis }) {
  const [showModal, setShowModal] = useState(false);
  const [modalData, setModalData] = useState([]);

  if (!analysis) return null;

  const {
    technical,
    fundamental,
    sentiment,
    recommendation,
    justification,
    meta,
    risks,
  } = analysis;

  // Fetch SEC reference docs when modal opens
  const handleOpenModal = () => {
    setShowModal(true);

    fetch("/api/reference-docs")
      .then((res) => res.json())
      .then((data) => {
              console.log("Fetched reference docs:", data); // 👈 HIER

        setModalData(Object.values(data).flat());

      })
      .catch((err) => {
        console.error("Failed to load reference docs:", err);
        setModalData([]);
      });
  };

  return (
    <div className="bg-white rounded shadow p-4 hover-box mb-4">
      {/* Header */}
      <div className="d-flex align-items-center mb-3" style={{ gap: 10 }}>
        <h4 className="fw-bold text-primary mb-0">AI Analysis Recommendation</h4>
      </div>

      {/* Analysis Sections */}
      <div className="row g-3">
        {/* Technical */}
        <div className="col-md-4">
          <div className="p-3 rounded bg-light border h-100">
            <div className="fw-bold mb-2" style={{ color: "#1e88e5" }}>
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
              Fundamental
            </div>
            <ul className="mb-0 small">
              {fundamental && fundamental.map((item, i) => <li key={i}>{item}</li>)}
            </ul>
          </div>
        </div>

        {/* Sentiment */}
        <div className="col-md-4">
          <div className="p-3 rounded bg-light border h-100">
            <div className="fw-bold mb-2" style={{ color: "#ff9800" }}>
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

      {/* Risks */}
      {risks && (
        <div className="alert alert-warning mt-4">
          <b>Risks:</b> {risks}
        </div>
      )}

      {/* Meta Preview */}
      <div className="mt-4 p-3 small bg-light border rounded position-relative">
        <div className="fw-bold mb-1 text-primary d-flex justify-content-between align-items-center">
          Meta Data SEC Files
          <button
            className="btn btn-sm btn-outline-primary"
            style={{ fontSize: 13 }}
            onClick={handleOpenModal}
          >
            Open Meta Data
          </button>
        </div>
        <div>
          
        </div>

        {/* Modal with dynamic reference data */}
        <SecFileModal
          data={modalData}
          show={showModal}
          onClose={() => setShowModal(false)}
        />
      </div>
    </div>
  );
}

export default RecommendationBox;
