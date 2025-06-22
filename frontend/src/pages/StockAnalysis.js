import { useEffect, useState } from "react";
import NewsCarousel from "../components/stockAnalysisPage/NewsCarousel";
import ParseBrokerAnalysis from "../utils/ParseBrokerAnalysis";
import RecommendationBox from "../components/stockAnalysisPage/RecommendationBox";
import AnalysisLoadingScreen from "../components/stockAnalysisPage/AnalysisLoadingScreen";
// import AnalysisChart from "../components/stockAnalysisPage/AnalysisChart";
import AnalysisChartGrafana from "../components/stockAnalysisPage/AnalysisChartGrafana";

function StockAnalysis() {
  const [news, setNews] = useState([]);
  const [loadingNews, setLoadingNews] = useState(true);
  const [modernAnalysis, setModernAnalysis] = useState(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState(true);
  const [forecastData, setForecastData] = useState(null);
  const [facts, setFacts] = useState(null); //for heading
  const params = new URLSearchParams(window.location.search);
  const ticker = params.get("company");

  useEffect(() => {
    if (!ticker) return;

    // delete cache before loading site
    fetch("/api/delete-cache").then(() => {
      console.log("Cache deleted");

      // ---------- COMPANY NEWS ----------
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

      // ---------- History & Forecast ----------

      fetch(`/api/forecast/${ticker}`)
        .then((res) => res.json())
        .then((data) => {
          setForecastData(data);
        })
        .catch((err) => console.error("Fehler beim Forecast:", err));

      // ---------- COMPANY DETAILS ---------
      // fetching facts to get company name for heading
      fetch(`/api/company-facts/${ticker}`)
        .then((res) => res.json())
        .then((data) => {
          console.log("Company facts:", data); // 👈 DEBUG
          setFacts(data);
        })
        .catch((err) =>
          console.error("Error loading the company information:", err)
        );

      // ---------- ANALYSIS ----------
      setLoadingAnalysis(true);
      const analysisController = new AbortController();
      fetch(`/api/stock-broker-analysis/${ticker}`, {
        signal: analysisController.signal,
      })
        .then((res) => res.json())
        .then((data) => {
          if (analysisController.signal.aborted) return;

          console.log("[/stock-broker-analysis API Response]:", data); // 🔍 DEBUG

          if (data) {
            const analysis = ParseBrokerAnalysis(data); // ❗ Direkt data (nicht data.broker_analysis)
            console.log("[Parsed Analysis]:", analysis); // 🔍 DEBUG
            setModernAnalysis(analysis);
          }
        })
        .catch((err) => {
          if (err.name !== "AbortError") setModernAnalysis(null);
        })
        .finally(() => {
          if (!analysisController.signal.aborted) setLoadingAnalysis(false);
        });

      // CLEAN-UP: Beide Fetches abbrechen, wenn Effect neu startet oder Komponente unmountet
      return () => {
        newsController.abort();
        analysisController.abort();
      };
    });
  }, [ticker]);

  return (
    <div className="container my-5">
      {/* Header */}
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

      {/* News-Carousel
      <NewsCarousel news={news} loading={loadingNews} /> */}

      {/* Charts & Recommendation */}
      {loadingAnalysis ? (
        <AnalysisLoadingScreen />
      ) : (
        <>
          {/* Charts & Simulation Placeholder */}
          <div className="mb-4">
            {ticker && <AnalysisChartGrafana ticker={ticker} />}
          </div>
          {/* Recommendation */}
          <div className="mt-4">
            <RecommendationBox analysis={modernAnalysis} />
          </div>
        </>
      )}

      {/* News-Carousel */}
      <NewsCarousel news={news} loading={loadingNews} />
    </div>
  );
}

export default StockAnalysis;
