function CompanyFacts({ facts }) {
  return (
    <div className="bg-light rounded shadow p-4 mb-5 hover-box">
      <h4 className="mb-4 text-secondary">📊 Company Snapshot</h4>
      <div className="row">
        <div className="col-md-6">
          <p><i className="fas fa-building text-primary me-2"></i><strong>Name:</strong> {facts.name}</p>
          <p><i className="fas fa-layer-group text-primary me-2"></i><strong>Sector:</strong> {facts.sector}</p>
          <p><i className="fas fa-industry text-primary me-2"></i><strong>Industry:</strong> {facts.industry}</p>
          <p><i className="fas fa-dollar-sign text-primary me-2"></i><strong>Current Price:</strong> ${facts.current_price.toFixed(2)}</p>
          <p><i className="fas fa-chart-line text-primary me-2"></i><strong>Market Cap:</strong> ${Math.round(facts.market_cap / 1e9)}B</p>
        </div>
        <div className="col-md-6">
          <p><i className="fas fa-coins text-primary me-2"></i><strong>EPS:</strong> {facts.eps_trailing}</p>
          <p><i className="fas fa-cash-register text-primary me-2"></i><strong>Revenue:</strong> ${Math.round(facts.revenue / 1e9)}B</p>
          <p><i className="fas fa-wallet text-primary me-2"></i><strong>Net Income:</strong> ${Math.round(facts.net_income / 1e9)}B</p>
          <p><i className="fas fa-percentage text-primary me-2"></i><strong>Dividend Yield:</strong> {facts.dividend_yield}%</p>
        </div>
      </div>
    </div>
  );
}

export default CompanyFacts;
