import { useEffect, useState } from "react";
import Select from "react-select";
import { FaTimes, FaFilter } from "react-icons/fa";

// Checkbox-Option für Screener-Filter
const CustomCheckboxOption = (props) => {
  const { data, isSelected, innerRef, innerProps } = props;
  return (
    <div
      ref={innerRef}
      {...innerProps}
      className="px-2 py-1 d-flex align-items-center"
      style={{ cursor: props.isDisabled ? "not-allowed" : "pointer" }}
    >
      <input
        type="checkbox"
        checked={isSelected}
        readOnly
        className="form-check-input me-2"
        disabled={props.isDisabled}
      />
      <label className="form-check-label mb-0 text-muted">{data.label}</label>
    </div>
  );
};

function SearchBarFilters({ companyList }) {
  const [screenerOptions, setScreenerOptions] = useState([]);
  const [selectedScreeners, setSelectedScreeners] = useState([]);
  const [marketCap, setMarketCap] = useState("");
  const [capUnit, setCapUnit] = useState("B");
  const [filteredCompanyList, setFilteredCompanyList] = useState([]);
  const [isFiltering, setIsFiltering] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState(null);

  const capUnitOptions = [
    { value: "M", label: "Million USD" },
    { value: "B", label: "Billion USD" },
    { value: "T", label: "Trillion USD" },
  ];

  const simplify = (str) =>
    str
      .trim()
      .toUpperCase()
      .replace(/[^A-Z0-9]/g, "");

  useEffect(() => {
    fetch("/api/screeners")
      .then((res) => res.json())
      .then((data) =>
        setScreenerOptions(
          data.map((s) => ({
            label: s.replace(/_/g, " ").toUpperCase(),
            value: s,
          }))
        )
      )
      .catch((err) => console.error("Failed to load screeners:", err));
  }, []);

  useEffect(() => {
    setFilteredCompanyList(companyList);
  }, [companyList]);

  const applyFilter = async () => {
    setIsFiltering(true);

    if (selectedScreeners.length === 0 || companyList.length === 0) {
      setFilteredCompanyList(companyList);
      setIsFiltering(false);
      return;
    }

    const screenersQuery = selectedScreeners
      .map((s) => `screeners=${encodeURIComponent(s.value)}`)
      .join("&");

    const unitMultipliers = {
      M: 1_000_000,
      B: 1_000_000_000,
      T: 1_000_000_000_000,
    };
    const numericCap = Number(marketCap);
    const capInUSD =
      !isNaN(numericCap) && capUnit in unitMultipliers
        ? numericCap * unitMultipliers[capUnit]
        : "";

    const url =
      capInUSD && capInUSD > 0
        ? `/api/second-filter-market-cap/?${screenersQuery}&min_cap=${capInUSD}`
        : `/api/filter-ticker-from-screener/?${screenersQuery}`;

    try {
      const res = await fetch(url);
      const data = await res.json();

      const tickers = Array.isArray(data.filtered)
        ? data.filtered.map((item) => (Array.isArray(item) ? item[1] : item))
        : Array.isArray(data)
        ? data
        : [];

      const cleanedSimplified = tickers.map(simplify);

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
    setSelectedScreeners([]);
    setMarketCap("");
    setCapUnit("B");
    setFilteredCompanyList(companyList);
  };

  return (
    <div className="text-center mt-4">
      {/* Search Field */}
      <div className="container mb-4" style={{ maxWidth: "700px" }}>
        <Select
          options={filteredCompanyList.map((company) => ({
            value: company.ticker,
            label: `${company.title} (${company.ticker})`,
          }))}
          value={selectedCompany}
          onChange={(selected) => setSelectedCompany(selected)}
          placeholder="🔍 Search company name..."
          isDisabled={isFiltering}
        />

        {isFiltering && (
          <div
            className="mb-3 d-flex justify-content-center align-items-center gap-2"
            style={{ marginTop: "1.5rem" }}
          >
            <div className="spinner-border text-primary" role="status" />
            <span className="text-muted">Loading filtered companies…</span>
          </div>
        )}
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
              {/* Screener Multi-Select */}
              <div className="col-12 col-md-6 text-start">
                <label className="form-label fw-semibold">Screener</label>
                <Select
                  options={screenerOptions}
                  value={selectedScreeners}
                  onChange={(selected) => {
                    if (!selected || selected.length <= 3) {
                      setSelectedScreeners(selected || []);
                    }
                  }}
                  isMulti
                  placeholder="Choose up to 3 screeners..."
                  isDisabled={isFiltering}
                  closeMenuOnSelect={false}
                  hideSelectedOptions={false}
                  classNamePrefix="react-select"
                  isOptionDisabled={(option) =>
                    selectedScreeners.length >= 3 &&
                    !selectedScreeners.some((s) => s.value === option.value)
                  }
                  components={{
                    Option: CustomCheckboxOption,
                    MultiValueRemove: () => null,
                  }}
                  styles={{
                    option: (provided, state) => ({
                      ...provided,
                      backgroundColor: state.isDisabled
                        ? "#f8f9fa"
                        : state.isSelected
                        ? "#e6f0ff"
                        : state.isFocused
                        ? "#f0f0f0"
                        : "#fff",
                      color: state.isDisabled ? "#ccc" : "#000",
                      cursor: state.isDisabled ? "not-allowed" : "default",
                    }),
                  }}
                />
                <small className="text-muted">
                  Max. 3 screeners can be selected
                </small>
              </div>

              {/* Market Cap */}
              <div className="col-12 col-md-6 text-start">
                <label className="form-label fw-semibold">
                  Market Cap (min)
                </label>
                <div className="d-flex flex-column flex-md-row align-items-stretch gap-2">
                  <input
                    type="number"
                    className="form-control"
                    placeholder="e.g. 2.5"
                    value={marketCap}
                    onChange={(e) => setMarketCap(e.target.value)}
                    disabled={selectedScreeners.length === 0 || isFiltering}
                    style={{
                      cursor:
                        selectedScreeners.length === 0 || isFiltering
                          ? "not-allowed"
                          : "text",
                      backgroundColor:
                        selectedScreeners.length === 0 || isFiltering
                          ? "#f8f9fa"
                          : "#fff",
                    }}
                  />
                  <div style={{ minWidth: "180px" }}>
                    <div
                      style={{
                        minWidth: "180px",
                        cursor:
                          selectedScreeners.length === 0 || isFiltering
                            ? "not-allowed"
                            : "default",
                      }}
                    >
                      <Select
                        options={capUnitOptions}
                        value={capUnitOptions.find(
                          (opt) => opt.value === capUnit
                        )}
                        onChange={(selected) => setCapUnit(selected.value)}
                        isDisabled={
                          selectedScreeners.length === 0 || isFiltering
                        }
                        isSearchable={false}
                        classNamePrefix="rs-capunit"
                      />
                    </div>
                  </div>
                </div>
                <div className="text-muted mt-1">
                  Current:{" "}
                  <strong>
                    {marketCap || "–"}{" "}
                    {capUnitOptions.find((u) => u.value === capUnit)?.label}
                  </strong>
                </div>
              </div>
            </div>
            <div className="d-flex justify-content-end mt-3">
              <button
                className="btn btn-primary"
                onClick={applyFilter}
                disabled={selectedScreeners.length === 0 || isFiltering}
              >
                Apply Filter
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Active Filter Badges */}
      {(selectedScreeners.length > 0 || marketCap) && (
        <div className="text-center mb-4">
          {selectedScreeners.map((s) => (
            <span className="badge bg-primary me-2" key={s.value}>
              {s.label}
              <FaTimes
                className="ms-2"
                style={{ cursor: "pointer" }}
                onClick={() =>
                  setSelectedScreeners((prev) =>
                    prev.filter((item) => item.value !== s.value)
                  )
                }
              />
            </span>
          ))}
          {marketCap && (
            <span className="badge bg-primary">
              Market Cap ≥ {marketCap}{" "}
              {capUnitOptions.find((u) => u.value === capUnit)?.label}
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
          onClick={() => {
            if (selectedCompany) {
              window.location.href = `/company?company=${selectedCompany.value}`;
            } else {
              alert("Please select a company first.");
            }
          }}
          disabled={isFiltering}
        >
          START BROKER
        </button>
      </div>
    </div>
  );
}

export default SearchBarFilters;
