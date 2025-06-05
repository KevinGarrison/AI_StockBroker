import { useEffect, useState } from "react";

function StockHistory() {
  const [data, setData] = useState(null);

  const params = new URLSearchParams(window.location.search);
  const ticker = params.get("company");

  useEffect(() => {
    if (!ticker) return;

    fetch(`/api/stock-history/${ticker}`)
      .then(res => res.json())
      .then(setData)
      .catch(err => console.error("Fehler beim Laden:", err));
  }, [ticker]);

  return (
    <div style={{ padding: "2rem", fontFamily: "monospace" }}>
      <h2>Stock History für: {ticker}</h2>
      {data ? (
        <pre>{JSON.stringify(data, null, 2)}</pre>
      ) : (
        <p>Lade Daten...</p>
      )}
    </div>
  );
}

export default StockHistory;
