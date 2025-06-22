import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";

function CompanyChart({ history }) {
  const chartRef = useRef(null);
  const wrapperRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 400 });

  // 📏 Containergröße beobachten
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

  // 📈 Chart zeichnen
  useEffect(() => {
    if (!history) return;

    const parsed = Object.entries(history).map(([date, value]) => ({
      date: new Date(date),
      value: +value,
    }));

    const svg = d3.select(chartRef.current);
    svg.selectAll("*").remove();

    const { width, height } = dimensions;

    // Dynamische Margin
    const margin = width < 500
      ? { top: 10, right: 10, bottom: 80, left: 50 }
      : { top: 20, right: 30, bottom: 70, left: 60 };

    const x = d3
      .scaleTime()
      .domain(d3.extent(parsed, (d) => d.date))
      .range([margin.left, width - margin.right]);

    const y = d3
      .scaleLinear()
      .domain([d3.min(parsed, (d) => d.value), d3.max(parsed, (d) => d.value)])
      .nice()
      .range([height - margin.bottom, margin.top]);

    const line = d3
      .line()
      .x((d) => x(d.date))
      .y((d) => y(d.value));

    // 📅 Dynamischer Tick-Intervall (X-Achse)
    let tickInterval;
    if (width < 400) {
      tickInterval = d3.timeYear.every(1); // jährlich
    } else if (width < 700) {
      tickInterval = d3.timeMonth.every(6); // halbjährlich
    } else {
      tickInterval = d3.timeMonth.every(3); // vierteljährlich
    }

    // 🕒 X-Achse
    svg
      .append("g")
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(
        d3.axisBottom(x)
          .ticks(tickInterval)
          .tickFormat(d3.timeFormat("%b %Y"))
      )
      .selectAll("text")
      .attr("transform", "rotate(-45)")
      .attr("dx", "0.5em")
      .attr("dy", "1em")
      .style("text-anchor", "end");

    // 📊 Y-Achse
    svg
      .append("g")
      .attr("transform", `translate(${margin.left},0)`)
      .style("font-size", "12px")
      .call(d3.axisLeft(y));

    // 📉 Linie
    svg
      .append("path")
      .datum(parsed)
      .attr("fill", "none")
      .attr("stroke", "#0d6efd")
      .attr("stroke-width", 2)
      .attr("d", line);
  }, [history, dimensions]);

  return (
    <div ref={wrapperRef} className="bg-white rounded shadow p-4 hover-box">
      <h4 className="mb-3 text-secondary">Stock Price Chart</h4>
      {!history ? (
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

export default CompanyChart;
