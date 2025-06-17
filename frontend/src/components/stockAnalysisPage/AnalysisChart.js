import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";

function AnalysisChart({ data }) {
  const chartRef = useRef(null);
  const wrapperRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 400 });

  // Resize beobachten
  useEffect(() => {
    const observer = new ResizeObserver((entries) => {
      if (!entries || entries.length === 0) return;
      const { width } = entries[0].contentRect;
      const height = width < 500 ? 450 : 400;
      setDimensions({ width, height });
    });
    if (wrapperRef.current) observer.observe(wrapperRef.current);
    return () => observer.disconnect();
  }, []);

  // Chart zeichnen
  useEffect(() => {
    if (!data?.history || !data?.forecast) return;

    const parseArray = (arr) =>
      arr.map((d) => ({
        date: new Date(d.ds),
        value: +d.y,
      }));

    const fullHistory = parseArray(data.history);
    const forecast = parseArray(data.forecast);

    const forecastStart = forecast[0]?.date;
    const cutoffDate = d3.timeMonth.offset(forecastStart, -12); // only last 12 months
    const zoomedHistory = fullHistory.filter((d) => d.date >= cutoffDate);
    const combined = [...zoomedHistory, ...forecast];

    const forecastStartDate =
      forecast.length > 0 ? new Date(forecast[0].date) : null;

    const svg = d3.select(chartRef.current);
    svg.selectAll("*").remove();

    const { width, height } = dimensions;

    const margin =
      width < 500
        ? { top: 10, right: 10, bottom: 80, left: 50 }
        : { top: 20, right: 30, bottom: 70, left: 60 };

    const x = d3
      .scaleTime()
      .domain(d3.extent(combined, (d) => d.date))
      .range([margin.left, width - margin.right]);

    const y = d3
      .scaleLinear()
      .domain([
        d3.min(combined, (d) => d.value),
        d3.max(combined, (d) => d.value),
      ])
      .nice()
      .range([height - margin.bottom, margin.top]);

    const line = d3
      .line()
      .x((d) => x(d.date))
      .y((d) => y(d.value));

    // Dynamischer Tick-Intervall
    let tickInterval;
    if (width < 400) {
      tickInterval = d3.timeMonth.every(6); // sehr klein: halbjährlich
    } else if (width < 700) {
      tickInterval = d3.timeMonth.every(3); // mittel: vierteljährlich
    } else {
      tickInterval = d3.timeMonth.every(1); // Desktop: monatlich ✅
    }

    svg
      .append("g")
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(
        d3.axisBottom(x).ticks(tickInterval).tickFormat(d3.timeFormat("%b %Y"))
      )
      .selectAll("text")
      .attr("transform", "rotate(-45)")
      .attr("dx", "0.5em")
      .attr("dy", "1em")
      .style("text-anchor", "end");

    svg
      .append("g")
      .attr("transform", `translate(${margin.left},0)`)
      .style("font-size", "12px")
      .call(d3.axisLeft(y));

    // Historischer Teil
    svg
      .append("path")
      .datum(
        combined.filter((d) => !forecastStartDate || d.date < forecastStartDate)
      )
      .attr("fill", "none")
      .attr("stroke", "#0d6efd")
      .attr("stroke-width", 2)
      .attr("d", line);

    // Forecast-Teil (gestrichelt)
    svg
      .append("path")
      .datum(
        combined.filter((d) => forecastStartDate && d.date >= forecastStartDate)
      )
      .attr("fill", "none")
      .attr("stroke", "#fd7e14")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "6,3")
      .attr("d", line);

    // Verbindungslinie zwischen letztem History- und erstem Forecast-Punkt
    if (forecastStartDate && zoomedHistory.length > 0 && forecast.length > 0) {
      const lastHistoryPoint = zoomedHistory[zoomedHistory.length - 1];
      const firstForecastPoint = forecast[0];

      svg
        .append("path")
        .datum([lastHistoryPoint, firstForecastPoint])
        .attr("fill", "none")
        .attr("stroke", "#fd7e14")
        .attr("stroke-width", 2)
        .attr("stroke-dasharray", "6,3")
        .attr("d", line);
    }
  }, [data, dimensions]);

  return (
    <div ref={wrapperRef} className="bg-white rounded shadow p-4 hover-box">
      <h4 className="fw-bold text-primary mb-4">Stock Price History & Forecast (Last 12M)</h4>
      {!data ? (
        <p>Lade Chart-Daten...</p>
      ) : (
        <svg
          ref={chartRef}
          width={dimensions.width}
          height={dimensions.height}
          viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
          preserveAspectRatio="xMidYMid meet"
        />
      )}
    </div>
  );
}

export default AnalysisChart;
