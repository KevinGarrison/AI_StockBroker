// Author: Lukas Hauser

import React, { useEffect, useState } from "react";

function NewsCarousel({ news, loading, interval = 8000 }) {
  const [current, setCurrent] = useState(0);

  // Auto-rotate through news items in given interval
  useEffect(() => {
    if (!news || news.length === 0) return;
    const timer = setInterval(() => {
      setCurrent((prev) => (prev + 1) % news.length);
    }, interval);
    return () => clearInterval(timer); // Cleanup on unmount
  }, [news, interval]);

  if (loading) {
    return null; // Show nothing while loading
  }

  if (!news || news.length === 0) {
    return (
      <div className="text-center my-4 text-muted">No news available.</div>
    );
  }

  const currentNews = news[current].content;

  return (
    <>
      {/* Embedded CSS for animation and style */}
      <style>
        {`
          .news-carousel {
            min-height: 90px;
            background: #f7f9fb;
            border-radius: 1rem;
            overflow: hidden;
            transition: box-shadow 0.2s;
          }
          .fade-in-right {
            animation: fadeInRight 0.5s;
          }
          @keyframes fadeInRight {
            from {
              opacity: 0;
              transform: translateX(60px);
            }
            to {
              opacity: 1;
              transform: translateX(0);
            }
          }
        `}
      </style>

      {/* News card with animated content */}
      <div
        className="card bg-white rounded shadow p-4 hover-box mb-4"
        style={{ minHeight: "150px" }}
      >
        {/* Header */}
        <div
          style={{
            letterSpacing: "2px",
            fontWeight: 700,
            color: "#1565c0",
            fontSize: "1.05rem",
            textTransform: "uppercase",
            marginBottom: 10,
            borderBottom: "2px solid #e3e7ed",
            paddingBottom: 6,
            display: "flex",
            alignItems: "center",
          }}
        >
          Company News
        </div>

        {/* News content with optional image */}
        <div className="d-flex align-items-center fade-in-right w-100">
          {currentNews.thumbnail?.resolutions?.[1]?.url && (
            <img
              src={currentNews.thumbnail.resolutions[1].url}
              alt=""
              className="me-3 rounded"
              style={{ width: 90, height: 70, objectFit: "cover" }}
            />
          )}

          {/* News text content */}
          <div style={{ flex: 1, minWidth: 0 }}>
            <a
              href={currentNews.clickThroughUrl?.url || "#"}
              target="_blank"
              rel="noopener noreferrer"
              className="fw-bold h6 mb-1 text-decoration-none"
              style={{
                color: "#1565c0",
                display: "block",
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
            >
              {currentNews.title}
            </a>

            {/* Source and publication date */}
            <div className="small text-secondary mb-1">
              {currentNews.provider?.displayName} –{" "}
              {new Date(currentNews.pubDate).toLocaleString()}
            </div>

            {/* Summary preview with ellipsis clamp */}
            <div
              className="small"
              style={{
                display: "-webkit-box",
                WebkitLineClamp: 2,
                WebkitBoxOrient: "vertical",
                overflow: "hidden",
                textOverflow: "ellipsis",
                minHeight: "2.6em",
                lineHeight: "1.3em",
                maxHeight: "2.6em",
              }}
            >
              {currentNews.summary || currentNews.description}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default NewsCarousel;
