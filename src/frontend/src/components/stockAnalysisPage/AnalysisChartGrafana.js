function AnalysisChartGrafana({ ticker }) {
  const now = Date.now();
  const from = now - 1 * 365 * 24 * 60 * 60 * 1000;
  const to = now + 5 * 30 * 24 * 60 * 60 * 1000;

  const grafanaUrl = `http://localhost:3000/d-solo/5ebe1847-cf11-4eda-9014-42397e806c97/history-and-forecast?orgId=1&panelId=1&theme=light&var-ticker=${ticker}&from=${from}&to=${to}`;

  return (
    <div className="bg-white rounded shadow p-4 hover-box">
      <h4 className="fw-bold text-primary mb-4">
        Stock Price History & Forecast
      </h4>
      <iframe
        src={grafanaUrl}
        width="100%"
        height="400"
        frameBorder="0"
        title="Grafana Analysis Chart"
      ></iframe>
    </div>
  );
}

export default AnalysisChartGrafana;
