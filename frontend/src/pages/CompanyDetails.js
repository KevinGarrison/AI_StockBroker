import { useEffect, useState } from "react";
import CompanyFacts from "../components/companyDetailsPage/CompanyFacts";
import CompanyChartGrafana from "../components/companyDetailsPage/CompanyChartGrafana";
import HomeButton from "../components/common/HomeButton";
import CompanyFactsLoadingScreen from "../components/companyDetailsPage/CompanyFactsLoadingScreen";


function CompanyDetails() {
  const [facts, setFacts] = useState(null);
  const params = new URLSearchParams(window.location.search);
  const ticker = params.get("company");

  useEffect(() => {
    if (!ticker) return;

    fetch(`/api/company-facts/${ticker}`)
      .then((res) => res.json())
      .then(setFacts)
      .catch((err) => console.error("Fehler beim Laden der Firmeninfos:", err));
  }, [ticker]);

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
      {/* Header */}
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

      {/* Facts and Chart */}
      {facts ? <CompanyFacts facts={facts} /> : <CompanyFactsLoadingScreen />}

      {ticker && <CompanyChartGrafana ticker={ticker} />}

      {/* AI Button */}
      <div className="text-center mt-5">
        <button className="btn-modern-primary" onClick={onAnalysisClick}>
          AI Analysis
        </button>
      </div>
    </div>
  );
}

export default CompanyDetails;
