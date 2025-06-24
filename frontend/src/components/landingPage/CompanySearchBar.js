import Select from "react-select";

function CompanySearchBar({ companyList, onSelectCompany }) {
  const options = companyList.map((company) => ({
    value: company.ticker,
    label: `${company.title} (${company.ticker})`,
  }));

  return (
    <div className="mb-4 w-50 mx-auto">
      <Select
        options={options}
        onChange={(selected) => {
          if (selected) {
            onSelectCompany(selected.value); // hand over ticker
          }
        }}
        placeholder="Search company..."
      />
    </div>
  );
}

export default CompanySearchBar;
