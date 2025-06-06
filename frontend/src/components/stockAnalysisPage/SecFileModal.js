function SecFileModal({ meta, show, onClose }) {
  if (!show) return null;
  return (
    <div className="modal fade show d-block" tabIndex="-1" style={{ background: "rgba(0,0,0,0.4)" }}>
      <div className="modal-dialog modal-dialog-centered">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">Meta Data SEC Files</h5>
            <button type="button" className="btn-close" aria-label="Close" onClick={onClose}></button>
          </div>
          <div className="modal-body">
            <p><b>Form:</b> {meta.form || "-"}</p>
            <p><b>Report Date:</b> {meta.reportDate || "-"}</p>
            <p><b>Accession Number:</b> {meta.accessionNumber || "-"}</p>
            <p><b>CIK:</b> {meta.cik || "-"}</p>
          </div>
          <div className="modal-footer">
            <button className="btn btn-secondary" onClick={onClose}>Close</button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SecFileModal;
