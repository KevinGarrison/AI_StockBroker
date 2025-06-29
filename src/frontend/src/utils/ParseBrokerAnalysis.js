export default function ParseBrokerAnalysis(data) {
  if (!data) return null;

  return {
    technical: [data.technical_analysis],
    fundamental: [data.fundamental_analysis],
    sentiment: [data.sentiment_analysis],
    recommendation: data.final_recommendation || "",
    justification: data.justification || "",
    meta: data.sec_metadata && data.sec_metadata.length > 0
      ? {
          form: data.sec_metadata[0].file_type || "",
          reportDate: data.sec_metadata[0].file_date || "",
          accessionNumber: data.sec_metadata[0].file_name || "",
        }
      : {},
    risks: data.risks_sec_files || "",
  };
}
