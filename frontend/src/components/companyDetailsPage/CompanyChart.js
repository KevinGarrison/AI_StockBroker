import { useEffect, useRef } from "react";
import * as d3 from "d3";

function CompanyChart({ history }) {
  const chartRef = useRef(null);

  useEffect(() => {
    if (!history) return;

    const parsed = Object.entries(history).map(([date, value]) => ({
      date: new Date(date),
      value: +value,
    }));

    const svg = d3.select(chartRef.current);
    svg.selectAll("*").remove();

    const width = 800;
    const height = 400;
    const margin = { top: 20, right: 30, bottom: 40, left: 50 };

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

    svg
      .append("g")
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x).ticks(10).tickFormat(d3.timeFormat("%b %Y")))
      .selectAll("text")
      .attr("transform", "rotate(-45)")
      .style("text-anchor", "end");

    svg
      .append("g")
      .attr("transform", `translate(${margin.left},0)`)
      .call(d3.axisLeft(y));

    svg
      .append("path")
      .datum(parsed)
      .attr("fill", "none")
      .attr("stroke", "#0d6efd")
      .attr("stroke-width", 2)
      .attr("d", line);
  }, [history]);

  return (
    <div className="bg-white rounded shadow p-4 hover-box">
      <h4 className="mb-3 text-secondary">📉 Stock Price Chart</h4>
      {!history ? <p>Lade Chart-Daten...</p> : <svg ref={chartRef} width={800} height={400}></svg>}
    </div>
  );
}

export default CompanyChart;
