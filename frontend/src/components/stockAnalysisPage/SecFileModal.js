function SecFileModal({ data, show, onClose, loading }) {
  if (!show) return null;

  // Öffnet ein Dokument in einem neuen Browser-Tab
  const openInNewTab = (html) => {
    const blob = new Blob([html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank");
  };

  return (
    <div
      className="modal fade show d-block"
      tabIndex="-1"
      style={{ background: "rgba(0,0,0,0.4)" }}
    >
      <div className="modal-dialog modal-dialog-centered modal-lg">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">SEC Files</h5>
            <button
              type="button"
              className="btn-close"
              aria-label="Close"
              onClick={onClose}
            ></button>
          </div>

          <div className="modal-body">
            {/* during loading */}
            {loading ? (
              <div className="text-center text-muted">
                Loading files...
              </div>

              // after laoding
            ) : data && data.length > 0 ? (
              <ul className="list-group">
                {data.map((doc, index) => (
                  <li
                    key={index}
                    className="list-group-item d-flex justify-content-between align-items-center"
                  >
                    <div>
                      <strong>{doc.form}</strong> – {doc.filename}
                    </div>
                    <button
                      className="btn btn-sm btn-outline-primary"
                      onClick={() => openInNewTab(doc.raw_content)}
                    >
                      Open report
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-muted">No SEC files available.</p>
            )}
          </div>

          {/* <div className="modal-footer">
            <button className="btn btn-secondary" onClick={onClose}>
              Close
            </button>
          </div> */}
        </div>
      </div>
    </div>
  );
}

export default SecFileModal;
