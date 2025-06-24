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
            value={
              typeof facts.revenue_growth === "number"
                ? `${(facts.revenue_growth * 100).toFixed(1)}%`
                : "N/A"
            }
          />
        </div>

        {/* Right column */}
        <div className="col-md-6">
          <FactRow
            icon="fa-dollar-sign"
            label="Current Price"
            value={`$${safeToFixed(facts.current_price, 2)}`}
          />
          <FactRow
            icon="fa-chart-line"
            label="Market Cap"
            value={
              typeof facts.market_cap === "number"
                ? `$${Math.round(facts.market_cap / 1e9)}B`
                : "N/A"
            }
          />
          <FactRow
            icon="fa-balance-scale"
            label="Forward P/E"
            value={safeToFixed(facts.forward_pe, 2)}
          />
          <FactRow
            icon="fa-percentage"
            label="Dividend Yield"
            value={
              typeof facts.dividend_yield === "number"
                ? `${(facts.dividend_yield * 100).toFixed(2)}%`
                : "N/A"
            }
          />
          <FactRow
            icon="fa-globe"
            label="Website"
            value={
              facts.website ? (
                <a href={facts.website} target="_blank" rel="noopener noreferrer">
                  {facts.website}
                </a>
              ) : (
                "N/A"
              )
            }
          />
        </div>
      </div>
    </div>
  );
}

// Helper to safely use .toFixed() on numbers
function safeToFixed(val, digits = 2, fallback = "N/A") {
  return typeof val === "number" ? val.toFixed(digits) : fallback;
}

// Reusable FactRow component
function FactRow({ icon, label, value }) {
  return (
    <div className="d-flex mb-2 align-items-center flex-nowrap">
      <div
        className="me-2 d-flex"
        style={{
          width: "20px",
          color: "#1e88e5",
          flexShrink: 0,
          lineHeight: "1.25",
          marginTop: "1px",
        }}
      >
        <i className={`fas ${icon}`} />
      </div>

      {/* Label + Value */}
      <div className="d-flex align-items-center flex-wrap w-100">
        <div
          style={{
            minWidth: "130px",
            fontWeight: "bold",
            marginRight: "8px",
            flexShrink: 0,
          }}
        >
          {label}:
        </div>

        <div
          style={{
            flex: 1,
            minWidth: 0,
            wordBreak: "break-word",
            overflowWrap: "break-word",
          }}
        >
          {value}
        </div>
      </div>
    </div>
  );
}


// without Icons

// function FactRow({ label, value }) {
//   return (
//     <div className="d-flex mb-2 align-items-start flex-nowrap">
//       {/* Label + Value */}
//       <div className="d-flex flex-wrap w-100">
//         <div
//           style={{
//             minWidth: "130px",
//             fontWeight: "bold",
//             marginRight: "8px",
//             flexShrink: 0,
//           }}
//         >
//           {label}:
//         </div>
//         <div
//           style={{
//             flex: 1,
//             minWidth: 0,
//             wordBreak: "break-word",
//             overflowWrap: "break-word",
//           }}
//         >
//           {value}
//         </div>
//       </div>
//     </div>
//   );
// }







export default CompanyFacts;
