// Author: Lukas Hauser

import { useEffect, useState } from "react";
import NewsCarousel from "../components/stockAnalysisPage/NewsCarousel";
import ParseBrokerAnalysis from "../utils/ParseBrokerAnalysis";
import RecommendationBox from "../components/stockAnalysisPage/RecommendationBox";
import AnalysisLoadingScreen from "../components/stockAnalysisPage/AnalysisLoadingScreen";
import AnalysisChartGrafana from "../components/stockAnalysisPage/AnalysisChartGrafana";
import HomeButton from "../components/common/HomeButton";

function StockAnalysis() {
  const [news, setNews] = useState([]);
  const [loadingNews, setLoadingNews] = useState(true);
  const [modernAnalysis, setModernAnalysis] = useState(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState(true);
  const [facts, setFacts] = useState(null); // used for displaying the company name
  const params = new URLSearchParams(window.location.search);
  const ticker = params.get("company");

  useEffect(() => {
    if (!ticker) return;

    // Clear cached analysis data before fetching
    fetch("/api/delete-cache").then(() => {
      console.log("Cache deleted");

      // --- Load company news ---
      setLoadingNews(true);
      const newsController = new AbortController();
      fetch(`/api/company-news/${ticker}`, { signal: newsController.signal })
        .then((res) => res.json())
        .then((data) => {
          if (!newsController.signal.aborted) setNews(data);
        })
        .catch((err) => {
          if (err.name !== "AbortError") setNews([]);
        })
        .finally(() => {
          if (!newsController.signal.aborted) setLoadingNews(false);
        });

      // --- Load company name for heading ---
      fetch(`/api/company-facts/${ticker}`)
        .then((res) => res.json())
        .then((data) => {
          console.log("Company facts:", data);
          setFacts(data);
        })
        .catch((err) =>
          console.error("Error loading the company information:", err)
        );

      // --- Load AI analysis (technical, fundamental, sentiment, etc.) ---
      setLoadingAnalysis(true);
      const analysisController = new AbortController();
      fetch(`/api/stock-broker-analysis/${ticker}`, {
        signal: analysisController.signal,
      })
        .then((res) => res.json())
        .then((data) => {
          if (analysisController.signal.aborted) return;

          console.log("[/stock-broker-analysis API Response]:", data);

          if (data) {
            const analysis = ParseBrokerAnalysis(data); // extract structured fields from markdown
            console.log("[Parsed Analysis]:", analysis);
            setModernAnalysis(analysis);
          }
        })
        .catch((err) => {
          if (err.name !== "AbortError") setModernAnalysis(null);
        })
        .finally(() => {
          if (!analysisController.signal.aborted) setLoadingAnalysis(false);
        });

      // Abort fetches on component unmount or ticker change
      return () => {
        newsController.abort();
        analysisController.abort();
      };
    });
  }, [ticker]);

  return (
    <div className="container my-5">
      <HomeButton />

      {/* Page heading */}
      <div className="text-center mb-5">
        <h1 className="fw-bold display-5 text-primary">Analysis</h1>

        {facts?.name && (
          <h2 className="fs-3 text-secondary fw-semibold">
            {facts.name}
            <span className="badge bg-secondary ms-2">{ticker}</span>
          </h2>
        )}

        <p className="text-muted">
          Historical, simulated future & recommendations
        </p>
      </div>

      {/* Show chart + recommendations or loading screen */}
      {loadingAnalysis ? (
        <AnalysisLoadingScreen />
      ) : (
        <>
          <div className="mb-4">
            {ticker && <AnalysisChartGrafana ticker={ticker} />}
          </div>
          <div className="mt-4">
            <RecommendationBox analysis={modernAnalysis} />
          </div>
        </>
      )}

      {/* News carousel at the bottom */}
      <NewsCarousel news={news} loading={loadingNews} />
    </div>
  );
}

export default StockAnalysis;
