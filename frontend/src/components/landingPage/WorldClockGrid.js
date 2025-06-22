function WorldClockGrid({ cities, times }) {
  return (
    <div className="row mb-5">
      {cities.map((city) => (
        <div
          className="col-12 col-md-4 mb-4 d-flex justify-content-center"
          key={city.name}
        >
          <div className="clock-box">
            <div
              className="clock-title"
              style={{
                fontSize: "20px",
                fontWeight: "500",
                color: "#555",
                marginBottom: "6px",
              }}
            >
              {city.name}
            </div>
            <div
              className="clock-time"
              style={{
                fontSize: "30px",
                fontWeight: "600",
                color: "#0d6efd",
              }}
            >
              {times[city.name]}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default WorldClockGrid;