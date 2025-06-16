import { useEffect, useState } from "react";
import Select from "react-select";
import { FaTimes } from "react-icons/fa";

function SearchBarFilters({ searchTerm, setSearchTerm, companyList }) {
  const [filters, setFilters] = useState([]);
  const [selectedFilter, setSelectedFilter] = useState(null);
  const [marketCap, setMarketCap] = useState("");
  const [filteredCompanyList, setFilteredCompanyList] = useState([]);

  // Lade Filterkategorien
  useEffect(() => {
    fetch("/api/first-filter-dropdown")
      .then((res) => res.json())
      .then((data) =>
        setFilters(
          data.map((f) => ({
            label: f.replace(/_/g, " ").toUpperCase(),
            value: f,
          }))
        )
      )
      .catch((err) => console.error("Filter fetch failed:", err));
  }, []);

  // Initialisiere gefilterte Liste mit allen Companies
  useEffect(() => {
    setFilteredCompanyList(companyList);
  }, [companyList]);

  // Filtere Companies, wenn sich Filter ändern
  useEffect(() => {
  const fetchFilteredCompanies = async () => {
    if (!selectedFilter || companyList.length === 0) {
      console.log("[DEBUG] Kein Filter aktiv oder companyList noch leer");
      setFilteredCompanyList(companyList);
      return;
    }

    console.log("[DEBUG] Aktiver Filter:", selectedFilter.value);

    try {
      const res = await fetch(`/api/tickers-for-screener/${selectedFilter.value}`);
      const tickers = await res.json();

      console.log("[DEBUG] Ticker vom Filter-Endpunkt:", tickers.slice(0, 10), "...");

      const matching = companyList.filter((c) =>
        tickers.map((t) => t.toUpperCase()).includes(c.ticker.toUpperCase())
      );

      console.log("[DEBUG] Anzahl gefundener Matching-Companies:", matching.length);
      if (matching.length === 0) {
        console.warn("[WARNUNG] Kein Match! Prüfe Ticker-Namen oder Backend-Antwort.");
      }

      setFilteredCompanyList(matching);
    } catch (err) {
      console.error("[FEHLER] Beim Filter-Fetch:", err);
      setFilteredCompanyList([]);
    }
  };

  fetchFilteredCompanies();
}, [selectedFilter, companyList]);


  const handleStart = async () => {
    // 1. Manuelle Eingabe prüfen
    if (searchTerm.trim()) {
      const selectedCompany = filteredCompanyList.find(
        (c) => c.title.toLowerCase() === searchTerm.trim().toLowerCase()
      );
      if (selectedCompany) {
        window.location.href = `/company?company=${selectedCompany.ticker}`;
        return;
      }
    }

    // 2. Falls Filter aktiv
    if (selectedFilter) {
      const url = marketCap
        ? `/api/second-filter-market-cap/${selectedFilter.value}/${marketCap}`
        : `/api/tickers-for-screener/${selectedFilter.value}`;

      try {
        const res = await fetch(url);
        const tickers = await res.json();

        if (tickers.length === 0) {
          alert("No companies found with selected filters.");
          return;
        }

        window.location.href = `/company?company=${tickers[0]}`;
        return;
      } catch (err) {
        console.error("Filter fetch error:", err);
        alert("An error occurred while applying filters.");
        return;
      }
    }

    alert("Please enter a company or select a filter.");
  };

  const resetFilters = () => {
    setSelectedFilter(null);
    setMarketCap("");
  };

  return (
    <div className="text-center mt-4">

      {/* 🔍 Suchfeld */}
      <div className="mb-4">
        <input
          type="text"
          className="form-control w-50 mx-auto"
          placeholder="🔍 Search company name..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          list="companies"
        />
        <datalist id="companies">
          {filteredCompanyList.map((company, idx) => (
            <option key={`${company.ticker}-${idx}`} value={company.title} />
          ))}
        </datalist>
      </div>

      {/* 📊 Filter: Kategorie */}
      <div className="container mb-3" style={{ maxWidth: 600 }}>
        <label className="form-label fw-semibold">Category Filter</label>
        <Select
          options={filters}
          value={selectedFilter}
          onChange={setSelectedFilter}
          isClearable
          placeholder="Choose a filter..."
        />
      </div>

      {/* 💰 Filter: Market Cap */}
      <div className="container mb-3" style={{ maxWidth: 600 }}>
        <label className="form-label fw-semibold">Minimum Market Cap (in Mio)</label>
        <input
          type="number"
          className="form-control"
          placeholder="e.g. 100000"
          value={marketCap}
          onChange={(e) => setMarketCap(e.target.value)}
        />
      </div>

      {/* 🏷️ Aktive Filter als Tags */}
      {(selectedFilter || marketCap) && (
        <div className="text-center mb-4">
          {selectedFilter && (
            <span className="badge bg-primary me-2">
              {selectedFilter.label}
              <FaTimes
                className="ms-2"
                style={{ cursor: "pointer" }}
                onClick={() => setSelectedFilter(null)}
              />
            </span>
          )}
          {marketCap && (
            <span className="badge bg-primary">
              Market Cap &gt; {marketCap}
              <FaTimes
                className="ms-2"
                style={{ cursor: "pointer" }}
                onClick={() => setMarketCap("")}
              />
            </span>
          )}
          {(selectedFilter || marketCap) && (
            <button className="btn btn-link ms-3 p-0" onClick={resetFilters}>
              Reset All
            </button>
          )}
        </div>
      )}

      {/* 🚀 Start-Button */}
      <div className="text-center mt-3">
        <button className="btn btn-primary btn-lg px-5" onClick={handleStart}>
          START BROKER
        </button>
      </div>
    </div>
  );
}

export default SearchBarFilters;
