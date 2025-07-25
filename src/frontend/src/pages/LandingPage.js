// Author: Lukas Hauser

import { useEffect, useState } from "react";
import StockLoadingScreen from "../components/landingPage/StockLoadingScreen";
import SearchBarFilters from "../components/landingPage/SearchBarFilter";
import WorldClockGridWrapper from "../components/landingPage/WorldClockGridWrapper";

function LandingPage() {
  const [companyList, setCompanyList] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch and sort company data on first load
  useEffect(() => {
    fetch("/api/companies-df")
      .then((res) => res.json())
      .then((json) => {
        const sorted = json.sort((a, b) => a.title.localeCompare(b.title));
        setCompanyList(sorted);
        setLoading(false);
        console.log("companyList loaded:", sorted.length);
      })
      .catch((err) => {
        console.error("API error:", err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="container py-5 text-center">
      {/* Page title and subtitle */}
      <h1 className="fw-bold display-5 text-primary mb-2">Stockbroker AI</h1>
      <p className="text-muted mb-5">
        Your intelligent gateway to the stock market
      </p>

      {/* Show loading screen or main content */}
      {loading ? (
        <StockLoadingScreen />
      ) : (
        <>
          <WorldClockGridWrapper /> {/* Live clocks for global markets */}
          <SearchBarFilters companyList={companyList} /> {/* Search bar with dropdown */}
        </>
      )}
    </div>
  );
}

export default LandingPage;
