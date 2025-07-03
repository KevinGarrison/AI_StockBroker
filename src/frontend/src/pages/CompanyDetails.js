// Author: Lukas Hauser

import { useEffect, useState } from "react";
import CompanyFacts from "../components/companyDetailsPage/CompanyFacts";
import CompanyChartGrafana from "../components/companyDetailsPage/CompanyChartGrafana";
import HomeButton from "../components/common/HomeButton";
import CompanyFactsLoadingScreen from "../components/companyDetailsPage/CompanyFactsLoadingScreen";

function CompanyDetails() {
  const [facts, setFacts] = useState(null);

  // Get ticker from URL (e.g. ?company=AAPL)
  const params = new URLSearchParams(window.location.search);
  const ticker = params.get("company");

  // Fetch company facts with ticker
  useEffect(() => {
    if (!ticker) return;

    fetch(`/api/company-facts/${ticker}`)
      .then((res) => res.json())
      .then(setFacts)
      .catch((err) => console.error("Error loading company facts:", err));
  }, [ticker]);

  // Navigate to AI analysis page
  const onAnalysisClick = () => {
    if (ticker) {
      window.location.href = `/analysis?company=${ticker}`;
    } else {
      alert("Company not found (ticker missing in URL)!");
    }
  };

  return (
    <div className="container my-5">
      <HomeButton />

      {/* Page Header */}
      <div className="text-center mb-5">
        <h1 className="fw-bold display-5 text-primary">Company Dashboard</h1>

        {facts && (
          <h2 className="fs-3 text-secondary fw-semibold">
            {facts.name}
            <span className="badge bg-secondary ms-2">{ticker}</span>
          </h2>
        )}

        <p className="text-muted">Live market chart & key financials</p>
      </div>

      {/* Show either facts or loading screen */}
      {facts ? <CompanyFacts facts={facts} /> : <CompanyFactsLoadingScreen />}

      {/* Chart via Grafana integration */}
      {ticker && <CompanyChartGrafana ticker={ticker} />}

      {/* Button to navigate to AI analysis page */}
      <div className="text-center mt-5">
        <button className="btn-modern-primary" onClick={onAnalysisClick}>
          AI Analysis
        </button>
      </div>
    </div>
  );
}

export default CompanyDetails;
