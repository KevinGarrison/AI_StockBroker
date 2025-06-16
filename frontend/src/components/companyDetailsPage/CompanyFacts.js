function CompanyFacts({ facts }) {
  return (
    <div className="bg-white rounded shadow p-4 mb-5 hover-box">
      <h4 className="mb-4 text-secondary">Company Snapshot</h4>
      <div className="row">
        {/* Left column */}
        <div className="col-md-6">
          {/* Name */}
          <div className="d-flex mb-2">
            <div className="me-2" style={{ minWidth: "20px", color: "#1e88e5" }}>
              <i className="fas fa-building"></i>
            </div>
            <div className="d-flex">
              <div style={{ minWidth: "120px" }}>
                <strong>Name:</strong>
              </div>
              <div>{facts.name}</div>
            </div>
          </div>

          {/* Sector */}
          <div className="d-flex mb-2">
            <div className="me-2" style={{ minWidth: "20px", color: "#1e88e5" }}>
              <i className="fas fa-layer-group"></i>
            </div>
            <div className="d-flex">
              <div style={{ minWidth: "120px" }}>
                <strong>Sector:</strong>
              </div>
              <div>{facts.sector}</div>
            </div>
          </div>

          {/* Industry */}
          <div className="d-flex mb-2">
            <div className="me-2" style={{ minWidth: "20px", color: "#1e88e5" }}>
              <i className="fas fa-industry"></i>
            </div>
            <div className="d-flex">
              <div style={{ minWidth: "120px" }}>
                <strong>Industry:</strong>
              </div>
              <div>{facts.industry}</div>
            </div>
          </div>

          {/* Current Price */}
          <div className="d-flex mb-2">
            <div className="me-2" style={{ minWidth: "20px", color: "#1e88e5" }}>
              <i className="fas fa-dollar-sign"></i>
            </div>
            <div className="d-flex">
              <div style={{ minWidth: "120px" }}>
                <strong>Current Price:</strong>
              </div>
              <div>${facts.current_price.toFixed(2)}</div>
            </div>
          </div>

          {/* Market Cap */}
          <div className="d-flex mb-2">
            <div className="me-2" style={{ minWidth: "20px", color: "#1e88e5" }}>
              <i className="fas fa-chart-line"></i>
            </div>
            <div className="d-flex">
              <div style={{ minWidth: "120px" }}>
                <strong>Market Cap:</strong>
              </div>
              <div>${Math.round(facts.market_cap / 1e9)}B</div>
            </div>
          </div>
        </div>

        {/* Right column */}
        <div className="col-md-6">
          {/* EPS */}
          <div className="d-flex mb-2">
            <div className="me-2" style={{ minWidth: "20px", color: "#1e88e5" }}>
              <i className="fas fa-coins"></i>
            </div>
            <div className="d-flex">
              <div style={{ minWidth: "120px" }}>
                <strong>EPS:</strong>
              </div>
              <div>{facts.eps_trailing}</div>
            </div>
          </div>

          {/* Revenue */}
          <div className="d-flex mb-2">
            <div className="me-2" style={{ minWidth: "20px", color: "#1e88e5" }}>
              <i className="fas fa-cash-register"></i>
            </div>
            <div className="d-flex">
              <div style={{ minWidth: "120px" }}>
                <strong>Revenue:</strong>
              </div>
              <div>${Math.round(facts.revenue / 1e9)}B</div>
            </div>
          </div>

          {/* Net Income */}
          <div className="d-flex mb-2">
            <div className="me-2" style={{ minWidth: "20px", color: "#1e88e5" }}>
              <i className="fas fa-wallet"></i>
            </div>
            <div className="d-flex">
              <div style={{ minWidth: "120px" }}>
                <strong>Net Income:</strong>
              </div>
              <div>${Math.round(facts.net_income / 1e9)}B</div>
            </div>
          </div>

          {/* Dividend Yield */}
          <div className="d-flex mb-2">
            <div className="me-2" style={{ minWidth: "20px", color: "#1e88e5" }}>
              <i className="fas fa-percentage"></i>
            </div>
            <div className="d-flex">
              <div style={{ minWidth: "120px" }}>
                <strong>Dividend Yield:</strong>
              </div>
              <div>{facts.dividend_yield}%</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CompanyFacts;
