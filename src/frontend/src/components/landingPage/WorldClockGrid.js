import './WorldClockGrid.css'

function WorldClockGrid({ cities, times }) {
  return (
    <div className="clock-grid">
      {cities.map((city) => (
        <div className="clock-box" key={city.name}>
          <div className="clock-title">{city.name}</div>
          <div className="clock-time">{times[city.name]}</div>
        </div>
      ))}
    </div>
  );
}

export default WorldClockGrid;