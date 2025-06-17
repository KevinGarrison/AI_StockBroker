import { useEffect, useState } from "react";
import Select from "react-select";
import { FaTimes } from "react-icons/fa";

function SearchBarFilters({ searchTerm, setSearchTerm, companyList }) {
  const [filters, setFilters] = useState([]);
  const [selectedFilter, setSelectedFilter] = useState(null);
  const [marketCap, setMarketCap] = useState("");
  const [filteredCompanyList, setFilteredCompanyList] = useState([]);
  const [isFiltering, setIsFiltering] = useState(false);

  const simplify = (str) =>
    str
      .trim()
      .toUpperCase()
      .replace(/[^A-Z0-9]/g, "");

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

  useEffect(() => {
    setFilteredCompanyList(companyList);

    // ⬇️ Debug-Prüfung, ob Ticker aus Filter-API fehlen
    const debugFilteredTickers = [
      "GE",
      "RTX",
      "LMT",
      "TDG",
      "GD",
      "NOC",
      "HWM",
      "LHX",
      "HEI-A",
      "HEI",
      "CW",
      "TXT",
      "BWXT",
      "SARO",
      "ERJ",
      "HII",
      "CAE",
      "LOAR",
      "MOG-A",
    ];
    const missing = debugFilteredTickers.filter(
      (t) => !companyList.some((c) => c.ticker === t)
    );
    console.warn("⚠️ FEHLENDE TICKER IN companyList:", missing);
  }, [companyList]);

  useEffect(() => {
    if (!selectedFilter) {
      setFilteredCompanyList(companyList);
      return;
    }
    applyFilter();
  }, [selectedFilter]);

  const applyFilter = async () => {
    setIsFiltering(true);

    if (!selectedFilter || companyList.length === 0) {
      setFilteredCompanyList(companyList);
      setIsFiltering(false);
      return;
    }

    const url = marketCap
      ? `/api/second-filter-market-cap/${selectedFilter.value}/${marketCap}`
      : `/api/tickers-for-screener/${selectedFilter.value}`;

    try {
      const res = await fetch(url);
      const tickers = await res.json();

      const cleanedTickers = tickers.map((t) =>
        t.replaceAll('"', "").trim().toUpperCase()
      );
      const cleanedSimplified = cleanedTickers.map(simplify);

      const matching = companyList.filter((c) =>
        cleanedSimplified.includes(simplify(c.ticker))
      );

      const unmatched = cleanedTickers.filter(
        (t) => !companyList.some((c) => simplify(c.ticker) === simplify(t))
      );
      console.log("Cleaned API tickers:", cleanedTickers);
      console.log(
        "Matching Companies:",
        matching.map((c) => `${c.ticker} | ${c.title}`)
      );
      if (unmatched.length > 0)
        console.warn("⚠️ Unmatched Tickers:", unmatched);
      const missingTickers = cleanedTickers.filter(
        (ticker) =>
          !companyList.some((c) => simplify(c.ticker) === simplify(ticker))
      );
      console.warn("⚠️ FEHLENDE TICKER IN companyList:", missingTickers);

      missingTickers.forEach((t) => {
        const possible = companyList.filter((c) =>
          simplify(c.ticker).includes(simplify(t))
        );
        console.log(
          `🔎 Kandidaten für "${t}":`,
          possible.map((c) => `${c.ticker} | ${c.title}`)
        );
      });
      setFilteredCompanyList(matching);
    } catch (err) {
      console.error("Could not fetch filtered companies:", err);
      setFilteredCompanyList([]);
    } finally {
      setIsFiltering(false);
    }
  };

  const resetFilters = () => {
    setSelectedFilter(null);
    setMarketCap("");
    setFilteredCompanyList(companyList);
  };

  const handleStart = async () => {
    if (searchTerm.trim()) {
      const selectedCompany = filteredCompanyList.find(
        (c) => c.title.trim().toLowerCase() === searchTerm.trim().toLowerCase()
      );
      if (selectedCompany) {
        window.location.href = `/company?company=${selectedCompany.ticker}`;
        return;
      }
    }

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

  return (
    <div className="text-center mt-4">
      {/* Suchfeld */}
      <div className="container mb-4" style={{ maxWidth: "700px" }}>
        <input
          type="text"
          className="form-control mx-auto"
          placeholder="🔍 Search company name..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          list="companies"
          disabled={isFiltering}
        />
        <datalist id="companies">
          {filteredCompanyList.map((company, idx) => (
            <option
              key={`${company.ticker}-${idx}`}
              value={company.title.trim()}
            />
          ))}
        </datalist>
      </div>

      {/* Ladeanzeige */}
      {isFiltering && (
        <div className="mb-3 d-flex justify-content-center align-items-center gap-2">
          <div className="spinner-border text-primary" role="status" />
          <span className="text-muted">Loading filtered companies…</span>
        </div>
      )}

      {/* Filter-Karte */}
      <div className="container mb-4" style={{ maxWidth: 700 }}>
        <div className="bg-white shadow rounded p-4 hover-box">
          <div className="row g-3 align-items-end">
            <div className="col-md-6 text-start">
              <label className="form-label fw-semibold">Category</label>
              <Select
                options={filters}
                value={selectedFilter}
                onChange={setSelectedFilter}
                isClearable
                placeholder="Choose a category..."
                className="border rounded"
                isDisabled={isFiltering}
              />
            </div>

            <div className="col-md-4 text-start">
              <label className="form-label fw-semibold">
                Market Cap (in Mio)
              </label>
              <div className="input-group">
                <span className="input-group-text bg-white border-end-0">
                  ≥
                </span>
                <input
                  type="number"
                  className="form-control border-start-0"
                  placeholder="e.g. 100000"
                  value={marketCap}
                  onChange={(e) => setMarketCap(e.target.value)}
                  disabled={isFiltering}
                />
              </div>
            </div>

            <div className="col-md-2 d-grid">
              <button
                className="btn btn-primary fw-semibold"
                onClick={applyFilter}
                disabled={isFiltering}
              >
                Apply
              </button>
            </div>
          </div>
        </div>
      </div>

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
          <button className="btn btn-link ms-3 p-0" onClick={resetFilters}>
            Reset All
          </button>
        </div>
      )}

      <div className="text-center mt-3">
        <button
          className="btn btn-primary btn-lg px-5"
          onClick={handleStart}
          disabled={isFiltering}
        >
          START BROKER
        </button>
      </div>
    </div>
  );
}

export default SearchBarFilters;
