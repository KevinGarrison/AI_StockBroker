import { useEffect, useState } from "react";
import StockLoadingScreen from "../components/landingPage/StockLoadingScreen";
import WorldClockGrid from "../components/landingPage/WorldClockGrid";
import SearchBarFilters from "../components/landingPage/SearchBarFilter";

const cities = [
  { name: "London", timezone: "Europe/London" },
  { name: "Berlin", timezone: "Europe/Berlin" },
  { name: "New York", timezone: "America/New_York" },
  { name: "Tokyo", timezone: "Asia/Tokyo" },
  { name: "Los Angeles", timezone: "America/Los_Angeles" },
  { name: "Sydney", timezone: "Australia/Sydney" },
];

function LandingPage() {
  const [times, setTimes] = useState({});
  const [searchTerm, setSearchTerm] = useState("");
  const [companyList, setCompanyList] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const updateTimes = () => {
      const now = {};
      cities.forEach((city) => {
        now[city.name] = new Date().toLocaleTimeString("en-US", {
          timeZone: city.timezone,
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        });
      });
      setTimes(now);
    };
    updateTimes();
    const interval = setInterval(updateTimes, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    fetch("/api/companies")
      .then((res) => res.json())
      .then((json) => {
        const parsed = typeof json === "string" ? JSON.parse(json) : json;
        setCompanyList(parsed);

        // ✅ DEBUG: Anzahl und Beispielticker loggen
        console.log("✅ companyList loaded:", parsed.length, "company");
        console.log(
          "🔍 Beispiel-Ticker aus companyList:",
          parsed.slice(0, 20).map((c) => c.ticker)
        );

        // Optional: Überprüfe z. B. auf einen bestimmten Ticker
        const check = ["TGT", "DG", "BJ", "TBBB"];
        check.forEach((ticker) => {
          const found = parsed.find((c) => c.ticker === ticker);
          if (!found) console.warn(`${ticker} is missing in companyList`);
        });

        console.log(
          "[DEBUG] Alle geladenen Ticker:",
          parsed.map((c) => c.ticker)
        );

        setLoading(false);
      })
      .catch((err) => {
        console.error("API error:", err);
        setLoading(false);
      });
  }, []);

  const handleStart = () => {
    if (!searchTerm.trim()) return;

    const selectedCompany = companyList.find(
      (c) => c.title.toLowerCase() === searchTerm.trim().toLowerCase()
    );

    if (selectedCompany) {
      window.location.href = `/company?company=${selectedCompany.ticker}`;
    } else {
      alert("Company not found");
    }
  };

  return (
    <div className="container py-5 text-center">
      <h1 className="fw-bold display-5 text-primary mb-2">Stockbroker AI</h1>
      <p className="text-muted mb-5">
        Your intelligent gateway to the stock market
      </p>

      {loading ? (
        <StockLoadingScreen />
      ) : (
        <>
          <WorldClockGrid cities={cities} times={times} />

          <SearchBarFilters
            searchTerm={searchTerm}
            setSearchTerm={setSearchTerm}
            companyList={companyList}
            onStart={handleStart}
          />
        </>
      )}
    </div>
  );
}

export default LandingPage;
