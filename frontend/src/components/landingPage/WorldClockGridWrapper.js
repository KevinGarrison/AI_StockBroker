import { useEffect, useState } from "react";
import WorldClockGrid from "./WorldClockGrid";

const cities = [
  { name: "London", timezone: "Europe/London" },
  { name: "Berlin", timezone: "Europe/Berlin" },
  { name: "New York", timezone: "America/New_York" },
  { name: "Tokyo", timezone: "Asia/Tokyo" },
  { name: "Los Angeles", timezone: "America/Los_Angeles" },
  { name: "Sydney", timezone: "Australia/Sydney" },
];

function WorldClockGridWrapper() {
  const [times, setTimes] = useState({});

  useEffect(() => {
    const updateTimes = () => {
      const now = {};
      cities.forEach((city) => {
        now[city.name] = new Date().toLocaleTimeString("en-US", {
          timeZone: city.timezone,
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        });
      });
      setTimes(now);
    };

    updateTimes();
    const interval = setInterval(updateTimes, 1000);
    return () => clearInterval(interval);
  }, []);

  return <WorldClockGrid cities={cities} times={times} />;
}

export default WorldClockGridWrapper;
