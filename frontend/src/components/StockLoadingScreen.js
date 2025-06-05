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
// import React from "react";

import React from "react";

function StockLoadingScreen() {
  return (
    <div className="text-center my-5">
      <div className="mb-4">
        <i
          className="fas fa-chart-line fa-2x text-primary"
          style={{
            animation: "pulse 1.2s ease-in-out infinite",
          }}
        ></i>
      </div>
      <h5 className="text-muted">Fetching stock market data...</h5>
      <p style={{ fontSize: "0.9rem", color: "#888" }}>
        Please wait while we prepare your investment dashboard.
      </p>

      <style>
        {`
          @keyframes pulse {
            0% { transform: scale(1); opacity: 0.75; }
            50% { transform: scale(1.12); opacity: 1; }
            100% { transform: scale(1); opacity: 0.75; }
          }
        `}
      </style>
    </div>
  );
}

export default StockLoadingScreen;



