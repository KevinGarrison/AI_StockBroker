// Author: Lukas Hauser

export default function ParseBrokerAnalysis(data) {
  if (!data) return null;

  return {
    // Wrap raw analysis fields as arrays for easier rendering in lists
    technical: [data.technical_analysis],
    fundamental: [data.fundamental_analysis],
    sentiment: [data.sentiment_analysis],

    // Recommendation summary and reasoning
    recommendation: data.final_recommendation || "",
    justification: data.justification || "",

    // Optional SEC metadata (only first entry used)
    meta: data.sec_metadata && data.sec_metadata.length > 0
      ? {
          form: data.sec_metadata[0].file_type || "",
          reportDate: data.sec_metadata[0].file_date || "",
          accessionNumber: data.sec_metadata[0].file_name || "",
        }
      : {},

    // Risk summary related to SEC files
    risks: data.risks_sec_files || "",
  };
}
