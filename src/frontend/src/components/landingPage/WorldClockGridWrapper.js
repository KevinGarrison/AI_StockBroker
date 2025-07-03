// Author: Lukas Hauser

import { useEffect, useState } from "react";
import WorldClockGrid from "./WorldClockGrid";

// Predefined list of cities with IANA timezones
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

  // Periodically update local time for each city every second
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

    updateTimes(); // initial call
    const interval = setInterval(updateTimes, 1000); // update every second

    return () => clearInterval(interval); // cleanup on unmount
  }, []);

  return <WorldClockGrid cities={cities} times={times} />;
}

export default WorldClockGridWrapper;
