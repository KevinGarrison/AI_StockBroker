function SearchBarFilters({ searchTerm, setSearchTerm, companyList, onStart }) {
  return (
    <div className="text-center mt-4">
      {/* Suchfeld */}
      <div className="mb-4">
        <input
          type="text"
          className="form-control search-input"
          placeholder="🔍 Search company name..."
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

      {/* Button */}
      <button className="btn-modern-primary" onClick={onStart}>
        🚀 START BROKER
      </button>
    </div>
  );
}

export default SearchBarFilters;
