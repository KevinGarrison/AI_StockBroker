import LandingPage from "./pages/LandingPage";
import CompanyDetails from "./pages/CompanyDetails";
import StockAnalysis from "./pages/StockAnalysis";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";

function App() {
  const pathname = window.location.pathname;

  if (pathname.startsWith("/company")) return <CompanyDetails />;
  if (pathname.startsWith("/analysis")) return <StockAnalysis />;
  return <LandingPage />;
}

export default App;
