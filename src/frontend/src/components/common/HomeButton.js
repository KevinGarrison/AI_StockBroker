// Author: Lukas Hauser

function HomeButton() {
  const goHome = () => {
    fetch("/api/delete-forecasts", { method: "POST" })
      .then((res) => {
        if (!res.ok) throw new Error("Failed to delete forecasts");
        console.log("Forecast deletion succeeded");
      })
      .catch((err) => {
        console.error("Forecast deletion failed:", err);
      })
      .finally(() => {
        window.location.href = "/";
      });
  };

  return (
    <button
      onClick={goHome}
      className="btn btn-primary position-fixed"
      style={{
        top: "20px",
        left: "20px",
        zIndex: 1050,
        borderRadius: "50%",
        width: "48px",
        height: "48px",
        boxShadow: "0 0.25rem 0.5rem rgba(0,0,0,0.2)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
      aria-label="Go home"
    >
      <i className="fas fa-home"></i>
    </button>
  );
}

export default HomeButton;
