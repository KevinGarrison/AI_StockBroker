import LandingPage from "./pages/LandingPage";
import CompanyDetails from "./pages/CompanyDetails";
import StockHistory from "./pages/StockHistory";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";

function App() {
  const pathname = window.location.pathname;

  if (pathname.startsWith("/company")) return <CompanyDetails />;
  if (pathname.startsWith("/stock")) return <StockHistory />;
  return <LandingPage />;
}

export default App;
