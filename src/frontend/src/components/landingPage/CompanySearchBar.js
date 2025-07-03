// Author: Lukas Hauser

import Select from "react-select";

function CompanySearchBar({ companyList, onSelectCompany }) {
  // Convert company list to react-select format
  const options = companyList.map((company) => ({
    value: company.ticker,
    label: `${company.title} (${company.ticker})`,
  }));

  return (
    <div className="mb-4 w-50 mx-auto">
      {/* Dropdown component using react-select */}
      <Select
        options={options}
        onChange={(selected) => {
          if (selected) {
            onSelectCompany(selected.value); // pass selected ticker to parent
          }
        }}
        placeholder="Search company..."
      />
    </div>
  );
}

export default CompanySearchBar;
