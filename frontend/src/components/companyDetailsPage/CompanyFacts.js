import { useEffect, useState } from "react";

function CompanyFacts({ facts }) {
  const [tickerMap, setTickerMap] = useState({});

  useEffect(() => {
    fetch("/api/companies-df")
      .then((res) => res.json())
      .then((data) => {
        const map = {};
        data.forEach((item) => {
          map[item.ticker] = item.title;
        });
        setTickerMap(map);
      })
      .catch((err) => {
        console.error("Error fetching company titles:", err);
      });
  }, []);

  const displayName = tickerMap[facts.ticker] || "Company Name";

  return (
    <div className="bg-white rounded shadow p-4 mb-5 hover-box">
      <h4 className="mb-4 text-secondary">Company Snapshot</h4>
      <div className="row">
        {/* Left column */}
        <div className="col-md-6">
          <FactRow icon="fa-building" label="Name" value={displayName} />
          <FactRow icon="fa-layer-group" label="Sector" value={facts.sector} />
          <FactRow icon="fa-industry" label="Industry" value={facts.industry} />
          <FactRow
            icon="fa-users"
            label="Employees"
            value={facts.employees?.toLocaleString() || "N/A"}
          />
          <FactRow
            icon="fa-chart-bar"
            label="Revenue Growth"
            value={`${(facts.revenue_growth * 100).toFixed(1)}%`}
          />
        </div>

        {/* Right column */}
        <div className="col-md-6">
          <FactRow
            icon="fa-dollar-sign"
            label="Current Price"
            value={`$${facts.current_price.toFixed(2)}`}
          />
          <FactRow
            icon="fa-chart-line"
            label="Market Cap"
            value={`$${Math.round(facts.market_cap / 1e9)}B`}
          />
          <FactRow
            icon="fa-balance-scale"
            label="Forward P/E"
            value={facts.forward_pe.toFixed(2)}
          />
          <FactRow
            icon="fa-percentage"
            label="Dividend Yield"
            value={`${(facts.dividend_yield * 100).toFixed(2)}%`}
          />
          <FactRow
            icon="fa-globe"
            label="Website"
            value={
              <a href={facts.website} target="_blank" rel="noopener noreferrer">
                {facts.website}
              </a>
            }
          />
        </div>
      </div>
    </div>
  );
}

// Reusable FactRow component
function FactRow({ icon, label, value }) {
  return (
    <div className="d-flex align-items-center mb-2">
      {/* Icon */}
      <div className="me-2" style={{ width: "20px", color: "#1e88e5" }}>
        <i className={`fas ${icon}`}></i>
      </div>

      {/* Label + Value container */}
      <div className="d-flex justify-content-start w-100">
        <div style={{ width: "130px", fontWeight: "bold" }}>{label}:</div>
        <div className="flex-grow-1 text-wrap" style={{ marginLeft: "8px" }}>
          {value}
        </div>
      </div>
    </div>
  );
}

export default CompanyFacts;
