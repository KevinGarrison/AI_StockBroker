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
  const [isLoadingModalData, setIsLoadingModalData] = useState(false);

  if (!analysis) return null;

  const {
    technical,
    fundamental,
    sentiment,
    recommendation,
    justification,
    risks,
  } = analysis;

  // Fetch SEC reference docs when modal opens
  const handleOpenModal = () => {
    const scrollbarWidth =
      window.innerWidth - document.documentElement.clientWidth;
    document.body.style.overflow = "hidden";
    document.body.style.paddingRight = `${scrollbarWidth}px`;
    setShowModal(true);

    setIsLoadingModalData(true);
    setModalData([]);

    fetch("/api/reference-docs")
      .then((res) => res.json())
      .then((data) => {
        console.log("Fetched reference docs:", data);
        const flat = Object.values(data).flat();

        // remove sec file duplicates based on accession + filename
        const uniqueDocs = [];
        const seen = new Set();

        for (const doc of flat) {
          const key = `${doc.accession}_${doc.filename}`; // unique id
          if (!seen.has(key)) {
            seen.add(key);
            uniqueDocs.push(doc);
          }
        }

        setModalData(uniqueDocs);
      })
      .catch((err) => {
        console.error("Failed to load reference docs:", err);
        setModalData([]);
      })
      .finally(() => {
        setIsLoadingModalData(false);
      });
  };

  const handleCloseModal = () => {
    document.body.style.overflow = "auto";
    document.body.style.paddingRight = "0px";
    setShowModal(false);
  };

  const handleDownload = () => {
    const params = new URLSearchParams(window.location.search);
    const ticker = params.get("company");

    if (!ticker) {
      alert("No ticker provided.");
      return;
    }

    fetch(`/api/download-broker-pdf/${ticker}`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to download PDF");
        return res.blob();
      })
      .then((blob) => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `AI_Analysis_${ticker}.pdf`; // dynamischer Dateiname
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      })
      .catch((err) => {
        console.error("Download error:", err);
        alert("Download failed.");
      });
  };

  return (
    <div
      className={`bg-white rounded shadow p-4 mb-4 ${
        showModal ? "hover-box-active" : "hover-box"
      }`}
    >
      {/* Header */}
      <div className="d-flex align-items-center mb-3" style={{ gap: 10 }}>
        <h4 className="fw-bold text-primary mb-0">
          AI Analysis Recommendation
        </h4>
      </div>

      {/* Analysis Sections */}
      <div className="row g-3">
        {/* Technical */}
        <div className="col-md-4">
          <div className="p-3 rounded bg-light border h-100">
            <div className="fw-bold text-primary mb-2">
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
            <div className="fw-bold text-primary mb-2">
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
            <div className="fw-bold text-primary mb-2">
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
        <div className="d-flex align-items-center mt-4 mb-3">
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
        <div className="alert alert-warning mt-3">
          <b>Risks:</b> {risks}
        </div>
      )}

      {/* Buttons */}
      <div className="d-flex justify-content-end flex-wrap gap-2 mt-4">
        <button
          className="btn btn-outline-primary d-flex align-items-center gap-2 btn-hover-scale"
          onClick={handleOpenModal}
        >
          <i className="fas fa-folder-open"></i>
          View SEC Files
        </button>

        <button
          className="btn btn-primary d-flex align-items-center gap-2 btn-hover-scale"
          onClick={handleDownload}
        >
          <i className="fas fa-download"></i>
          Download AI Analysis
        </button>
      </div>

      {/* Modal with dynamic reference data */}
      <SecFileModal
        data={modalData}
        loading={isLoadingModalData}
        show={showModal}
        onClose={handleCloseModal}
      />
    </div>
  );
}

export default RecommendationBox;
