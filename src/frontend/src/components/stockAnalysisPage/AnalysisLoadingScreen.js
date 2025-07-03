// Author: Lukas Hauser

function AnalysisLoadingScreen() {
  return (
    <div className="text-center my-5">
      <div className="mb-4">
        <i className="fa-solid fa-money-bill-trend-up fa-beat-fade fa-2xl text-primary"></i>
      </div>
      <h5 className="text-muted">Loading company analysis...</h5>
      <p style={{ fontSize: "0.9rem", color: "#888" }}>
        The AI is evaluating financial data and recommendations.<br />
        Please hold on a moment!
      </p>
    </div>
  );
}

export default AnalysisLoadingScreen;