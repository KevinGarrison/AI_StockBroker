import { useEffect, useState } from "react";
import "bootstrap/dist/css/bootstrap.min.css";

const cities = [
  { name: "London", timezone: "Europe/London" },
  { name: "Berlin", timezone: "Europe/Berlin" },
  { name: "New York", timezone: "America/New_York" },
  { name: "Tokyo", timezone: "Asia/Tokyo" },
  { name: "Los Angeles", timezone: "America/Los_Angeles" },
  { name: "Sydney", timezone: "Australia/Sydney" },
];

function App() {
  const [times, setTimes] = useState({});
  const [searchTerm, setSearchTerm] = useState("");
  const [companyList, setCompanyList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState(0);

  // Uhrzeiten aktualisieren
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

  // Lade Firmen-Daten von deinem Backend
  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => (prev < 90 ? prev + 1 : prev));
    }, 90);

    fetch("/api/")
      .then((res) => res.json())
      .then((json) => {
        // Falls json ein String ist (also nochmal geparst werden muss)
        const parsed = typeof json === "string" ? JSON.parse(json) : json;
        setCompanyList(parsed);

        setProgress(100);
        setTimeout(() => setLoading(false), 300);
        clearInterval(interval);
      })
      .catch((err) => {
        console.error("API error:", err);
        setLoading(false);
        clearInterval(interval);
      });

    return () => clearInterval(interval);
  }, []);

  // Start Broker Button
  const handleStart = () => {
    if (searchTerm.trim()) {
      window.location.href = `/broker?company=${encodeURIComponent(
        searchTerm
      )}`;
    }
  };

  return (
    <div style={{ backgroundColor: "#f0f2f5", minHeight: "100vh" }}>
      <div className="container py-5 text-center">
        <h1 className="mb-4">Stockbroker AI</h1>

        {/* der Rest bleibt gleich */}

        {/* Ladeanzeige */}
        {loading ? (
          <div className="text-center">
            <p className="lead mb-3">Loading data from backend...</p>
            <div className="progress" style={{ height: "25px" }}>
              <div
                className="progress-bar progress-bar-striped progress-bar-animated bg-success"
                role="progressbar"
                style={{ width: `${progress}%` }}
                aria-valuenow={progress}
                aria-valuemin="0"
                aria-valuemax="100"
              >
                {progress}%
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* Städte-Uhren */}
            <div className="row mb-5">
              {cities.map((city) => (
                <div
                  className="col-12 col-md-4 mb-4 d-flex justify-content-center"
                  key={city.name}
                >
                  <div className="clock-box">
                    <div className="clock-title">{city.name}</div>
                    <div className="clock-time">{times[city.name]}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Suchfeld */}
            <div className="mb-3">
              <input
                type="text"
                className="form-control w-50 mx-auto"
                placeholder="Search company name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                list="companies"
              />
              <datalist id="companies">
                {companyList.map((company) => (
                  <option key={company.cik_str} value={company.title} />
                ))}
              </datalist>
            </div>

            {/* Start Button */}
            <button className="btn btn-primary" onClick={handleStart}>
              START BROKER
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default App;
