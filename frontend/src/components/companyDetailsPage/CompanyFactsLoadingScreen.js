function CompanyFactsLoadingScreen() {
  return (
    <div className="bg-white rounded shadow p-4 mb-5">
      <div className="placeholder-glow mb-2">
        <span className="placeholder col-6"></span>
      </div>
      {[...Array(5)].map((_, i) => (
        <div key={i} className="placeholder-glow mb-2">
          <span className="placeholder col-8"></span>
        </div>
      ))}
    </div>
  );
}

export default CompanyFactsLoadingScreen;
