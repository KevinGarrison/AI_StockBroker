import ReactDOM from "react-dom";

function SecFileModal({ data, show, onClose, loading }) {
  
  if (!show) return null;

  // Opens the document in a new tab
  const openInNewTab = (html) => {
    const blob = new Blob([html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank");
  };

  return ReactDOM.createPortal(
    <div
      className="modal show"
      tabIndex="-1"
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: "rgba(0,0,0,0.4)",
        overflowY: "auto",
        zIndex: 1055,
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "center",
        padding: "1rem",
      }}
    >
      <div
        className="modal-dialog modal-lg"
        style={{
          width: "100%",
          maxWidth: "700px",
          marginTop: "3rem",
        }}
      >
        <div className="modal-content" style={{ overflow: "hidden" }}>
          <div className="modal-header">
            <h5 className="modal-title">SEC Files</h5>
            <button
              type="button"
              className="btn-close"
              aria-label="Close"
              onClick={onClose}
            ></button>
          </div>

          <div
            className="modal-body"
            style={{
              maxHeight: "70vh",
              overflowY: "auto",
            }}
          >
            {loading ? (
              <div className="text-center text-muted">Loading files...</div>
            ) : data && data.length > 0 ? (
              <ul className="list-group">
                {data.map((doc, index) => (
                  <li
                    key={index}
                    className="list-group-item d-flex flex-column flex-md-row justify-content-between align-items-md-center"
                  >
                    <div className="flex-grow-1 text-break me-md-3">
                      <strong>{doc.form}</strong> – {doc.filename}
                    </div>

                    <button
                      className="btn btn-sm btn-outline-primary mt-2 mt-md-0"
                      style={{ minWidth: "120px" }}
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
        </div>
      </div>
    </div>,
    document.body
  );
}

export default SecFileModal;
