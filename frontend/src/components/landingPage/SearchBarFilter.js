import { useEffect, useState } from "react";
import Select from "react-select";
import { FaTimes, FaFilter } from "react-icons/fa";

function SearchBarFilters({ searchTerm, setSearchTerm, companyList }) {
  const [filters, setFilters] = useState([]);
  const [selectedFilter, setSelectedFilter] = useState(null);
  const [marketCap, setMarketCap] = useState("");
  const [capUnit, setCapUnit] = useState("B");
  const [filteredCompanyList, setFilteredCompanyList] = useState([]);
  const [isFiltering, setIsFiltering] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  const capUnitOptions = [
    { value: "M", label: "Million USD" },
    { value: "B", label: "Billion USD" },
    { value: "T", label: "Trillion USD" },
  ];

  const simplify = (str) =>
    str.trim().toUpperCase().replace(/[^A-Z0-9]/g, "");

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
  }, [companyList]);

  const applyFilter = async () => {
    setIsFiltering(true);

    if (!selectedFilter || companyList.length === 0) {
      setFilteredCompanyList(companyList);
      setIsFiltering(false);
      return;
    }

    const unitMultipliers = {
      M: 1,
      B: 1000,
      T: 1_000_000,
    };

    const numericCap = Number(marketCap);
    const capInMillion =
      !isNaN(numericCap) && capUnit in unitMultipliers
        ? numericCap * unitMultipliers[capUnit]
        : "";

    const url = capInMillion
      ? `/api/second-filter-market-cap/${selectedFilter.value}/${capInMillion}`
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
    setCapUnit("B");
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

    if (filteredCompanyList.length > 0) {
      window.location.href = `/company?company=${filteredCompanyList[0].ticker}`;
      return;
    }

    alert("Please enter a company or select a filter.");
  };

  return (
    <div className="text-center mt-4">
      {/* Search Input */}
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

      {/* Toggle Filter Button */}
      <div className="mb-3">
        <button
          className="btn btn-outline-secondary d-inline-flex align-items-center gap-2"
          onClick={() => setShowFilters((prev) => !prev)}
        >
          <FaFilter /> Filters
        </button>
      </div>

      {/* Filter Box */}
      {showFilters && (
        <div className="container mb-4" style={{ maxWidth: 700 }}>
          <div className="bg-white shadow rounded p-4 hover-box">
            <div className="row g-3 align-items-stretch">
              {/* Category */}
              <div className="col-12 col-md-6 text-start">
                <label className="form-label fw-semibold">Category</label>
                <Select
                  options={filters}
                  value={selectedFilter}
                  onChange={setSelectedFilter}
                  isClearable
                  placeholder="Choose a category..."
                  isDisabled={isFiltering}
                />
              </div>

              {/* Market Cap */}
              <div className="col-12 col-md-6 text-start">
                <label className="form-label fw-semibold">Market Cap (min)</label>
                <div className="d-flex flex-column flex-md-row align-items-stretch gap-2">
                  <input
                    type="number"
                    className="form-control"
                    placeholder="e.g. 2.5"
                    value={marketCap}
                    onChange={(e) => setMarketCap(e.target.value)}
                    disabled={!selectedFilter || isFiltering}
                  />
                  <div style={{ minWidth: "180px" }}>
                    <Select
                      options={capUnitOptions}
                      value={capUnitOptions.find((opt) => opt.value === capUnit)}
                      onChange={(selected) => setCapUnit(selected.value)}
                      isDisabled={!selectedFilter || isFiltering}
                      isSearchable={false}
                      styles={{ control: (base) => ({ ...base, height: "100%" }) }}
                    />
                  </div>
                </div>
                <div className="text-muted mt-1">
                  Current: <strong>{marketCap || "–"} { {
                    M: "Million",
                    B: "Billion",
                    T: "Trillion"
                  }[capUnit]} USD</strong>
                </div>
              </div>
            </div>
            <div className="d-flex justify-content-end mt-3">
              <button
                className="btn btn-primary"
                onClick={applyFilter}
                disabled={!selectedFilter || isFiltering}
              >
                Apply Filter
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Active Filter Badges */}
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
              Market Cap ≥ {marketCap} { {
                M: "Million",
                B: "Billion",
                T: "Trillion"
              }[capUnit] }
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

      {/* Start Button */}
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
