// Author: Lukas Hauser

function StockLoadingScreen() {
  return (
    <div className="text-center my-5">
      {/* Animated loading icon */}
      <div className="mb-4">
        <i className="fa-solid fa-chart-line fa-2xl fa-beat-fade text-primary"></i>
      </div>

      {/* Loading messages */}
      <h5 className="text-muted">Fetching stock market data...</h5>
      <p style={{ fontSize: "0.9rem", color: "#888" }}>
        Please wait while we prepare your investment dashboard.
      </p>
    </div>
  );
}

export default StockLoadingScreen;
