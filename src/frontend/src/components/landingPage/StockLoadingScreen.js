// import React from "react";

// function StockLoadingScreen() {
//   return (
//     <div className="text-center my-5">
//       <div className="mb-4">
//         <i className="fas fa-coins fa-2x text-primary fa-spin"></i>
//       </div>
//       <h5 className="text-muted">Fetching stock market data...</h5>
//       <p style={{ fontSize: "0.9rem", color: "#888" }}>
//         Please wait while we prepare your investment dashboard.
//       </p>
//     </div>
//   );
// }

// export default StockLoadingScreen;

function StockLoadingScreen() {
  return (
    <div className="text-center my-5">
      <div className="mb-4">
        <i
          className="fa-solid fa-chart-line fa-2xl fa-beat-fade text-primary"
        ></i>
      </div>
      <h5 className="text-muted">Fetching stock market data...</h5>
      <p style={{ fontSize: "0.9rem", color: "#888" }}>
        Please wait while we prepare your investment dashboard.
      </p>

    </div>
  );
}

export default StockLoadingScreen;



