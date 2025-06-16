import { useEffect, useState } from "react";
import NewsCarousel from "../components/stockAnalysisPage/NewsCarousel";
import ParseBrokerAnalysis from "../utils/ParseBrokerAnalysis";
import RecommendationBox from "../components/stockAnalysisPage/RecommendationBox";
import AnalysisLoadingScreen from "../components/stockAnalysisPage/AnalysisLoadingScreen";

function StockAnalysis() {
  const [news, setNews] = useState([]);
  const [loadingNews, setLoadingNews] = useState(true);
  const [modernAnalysis, setModernAnalysis] = useState(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState(true);
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
        <h1 className="fw-bold display-5 text-primary">Analysis: {ticker}</h1>
        <p className="text-muted">
          Historical, simulated future & recommendations
        </p>
      </div>

      {/* News-Carousel */}
      <NewsCarousel news={news} loading={loadingNews} />

      {/* Charts & Recommendation */}
      {loadingAnalysis ? (
        <AnalysisLoadingScreen />
      ) : (
        <>
          {/* Charts & Simulation Placeholder */}
          <div className="mb-4">
            <div className="alert alert-info">
              [Kursverlauf, simulierte Zukunft etc.]
            </div>
          </div>
          {/* Recommendation */}
          <div className="mt-4">
            <RecommendationBox analysis={modernAnalysis} />
          </div>
        </>
      )}
    </div>
  );
}

export default StockAnalysis;
