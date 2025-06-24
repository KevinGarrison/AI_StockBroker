function CompanyChartGrafana({ ticker }) {
  const grafanaUrl = `http://44.202.117.18:3000/d-solo/eepq24k87rpc0e/new-dashboard?orgId=1&timezone=browser&theme=light&panelId=1&__feature.dashboardSceneSolo&var-ticker=${ticker}&from=now-10y&to=now`;

  return (
    <div className="bg-white rounded shadow p-4 hover-box">
      <h4 className="mb-3 text-secondary">Stock Price Chart</h4>
      <iframe
        src={grafanaUrl}
        width="100%"
        height="400"
        frameBorder="0"
        title="Grafana Stock Chart"
      ></iframe>
    </div>
  );
}

export default CompanyChartGrafana;
